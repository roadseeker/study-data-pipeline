#!/usr/bin/env bash

set -euo pipefail

# Rebuild local-only NiFi TLS assets with the current PC's mkcert root CA.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TLS_DIR="${TLS_DIR:-${REPO_ROOT}/config/nifi/tls}"
CERT_FILE="${TLS_DIR}/localhost+2.pem"
KEY_FILE="${TLS_DIR}/localhost+2-key.pem"
KEYSTORE_FILE="${TLS_DIR}/nifi-keystore.p12"
TRUSTSTORE_FILE="${TLS_DIR}/nifi-truststore.p12"
KEYSTORE_PASSWORD="${KEYSTORE_PASSWORD:-changeit}"
TRUSTSTORE_PASSWORD="${TRUSTSTORE_PASSWORD:-changeit}"
MKCERT_CERT_FILE="${CERT_FILE}"
MKCERT_KEY_FILE="${KEY_FILE}"

find_command() {
  local name="$1"
  shift

  if command -v "${name}" >/dev/null 2>&1; then
    command -v "${name}"
    return 0
  fi

  local candidate

  for candidate in "$@"; do
    if [ -x "${candidate}" ]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done

  return 1
}

normalize_exec_path() {
  local path="$1"

  path="${path//\\//}"

  if [[ "${path}" =~ ^([A-Za-z]):/(.*)$ ]]; then
    local drive="${BASH_REMATCH[1],,}"
    local rest="${BASH_REMATCH[2]}"

    if [ -d "/mnt/${drive}" ]; then
      printf '/mnt/%s/%s\n' "${drive}" "${rest}"
      return 0
    fi

    if [ -d "/${drive}" ]; then
      printf '/%s/%s\n' "${drive}" "${rest}"
      return 0
    fi
  fi

  printf '%s\n' "${path}"
}

to_windows_path() {
  local path="$1"

  if [[ "${path}" =~ ^/mnt/([a-z])/(.*)$ ]]; then
    local drive="${BASH_REMATCH[1]^}"
    printf '%s:/%s\n' "${drive}" "${BASH_REMATCH[2]}"
    return 0
  fi

  if [[ "${path}" =~ ^/([a-z])/(.*)$ ]]; then
    local drive="${BASH_REMATCH[1]^}"
    printf '%s:/%s\n' "${drive}" "${BASH_REMATCH[2]}"
    return 0
  fi

  printf '%s\n' "${path//\\//}"
}

find_via_powershell() {
  local name="$1"
  local resolved=""

  if ! command -v powershell.exe >/dev/null 2>&1; then
    return 1
  fi

  resolved="$(powershell.exe -NoProfile -Command "(Get-Command ${name} -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Source)" 2>/dev/null | tr -d '\r')"

  if [ -n "${resolved}" ]; then
    normalize_exec_path "${resolved}"
    return 0
  fi

  return 1
}

find_mkcert() {
  local candidates=(
    "/c/Users/${USERNAME:-}/AppData/Local/Microsoft/WinGet/Links/mkcert.exe"
    "C:/Users/${USERNAME:-}/AppData/Local/Microsoft/WinGet/Links/mkcert.exe"
  )

  if [ -n "${LOCALAPPDATA:-}" ]; then
    candidates+=("${LOCALAPPDATA//\\//}/Microsoft/WinGet/Links/mkcert.exe")
  fi

  if find_via_powershell mkcert; then
    return 0
  fi

  if find_command mkcert "${candidates[@]}"; then
    return 0
  fi

  echo "ERROR: mkcert was not found. Install mkcert and retry." >&2
  exit 1
}

find_openssl() {
  local candidates=(
    "/c/Program Files/Git/usr/bin/openssl.exe"
    "/c/Program Files/Git/mingw64/bin/openssl.exe"
    "/c/Program Files/OpenSSL-Win64/bin/openssl.exe"
    "C:/Program Files/Git/usr/bin/openssl.exe"
    "C:/Program Files/Git/mingw64/bin/openssl.exe"
    "C:/Program Files/OpenSSL-Win64/bin/openssl.exe"
  )

  if find_via_powershell openssl; then
    return 0
  fi

  if find_command openssl "${candidates[@]}"; then
    return 0
  fi

  echo "ERROR: openssl was not found. Install Git for Windows or OpenSSL and retry." >&2
  exit 1
}

MKCERT_BIN="$(find_mkcert)"
OPENSSL_BIN="$(find_openssl)"

if [[ "${MKCERT_BIN}" == *.exe ]]; then
  MKCERT_CERT_FILE="$(to_windows_path "${CERT_FILE}")"
  MKCERT_KEY_FILE="$(to_windows_path "${KEY_FILE}")"
fi

mkdir -p "${TLS_DIR}"

echo "============================================"
echo " Nexus Pay NiFi local TLS regeneration"
echo " TLS dir: ${TLS_DIR}"
echo " mkcert: ${MKCERT_BIN}"
echo " openssl: ${OPENSSL_BIN}"
echo "============================================"

echo "[1/4] Installing or refreshing the local mkcert CA"
"${MKCERT_BIN}" -install >/dev/null

CAROOT="$(normalize_exec_path "$("${MKCERT_BIN}" -CAROOT)")"
ROOT_CA_FILE="${CAROOT}/rootCA.pem"

if [ ! -f "${ROOT_CA_FILE}" ]; then
  echo "ERROR: mkcert root CA not found at ${ROOT_CA_FILE}" >&2
  exit 1
fi

echo "[2/4] Removing previous local TLS artifacts"
rm -f "${CERT_FILE}" "${KEY_FILE}" "${KEYSTORE_FILE}" "${TRUSTSTORE_FILE}"

echo "[3/4] Generating localhost certificate"
"${MKCERT_BIN}" \
  -cert-file "${MKCERT_CERT_FILE}" \
  -key-file "${MKCERT_KEY_FILE}" \
  localhost 127.0.0.1 ::1

echo "[4/4] Building NiFi keystore and truststore"
"${OPENSSL_BIN}" pkcs12 -export \
  -inkey "${KEY_FILE}" \
  -in "${CERT_FILE}" \
  -certfile "${ROOT_CA_FILE}" \
  -out "${KEYSTORE_FILE}" \
  -name nifi-key \
  -passout "pass:${KEYSTORE_PASSWORD}"

"${OPENSSL_BIN}" pkcs12 -export \
  -nokeys \
  -in "${ROOT_CA_FILE}" \
  -out "${TRUSTSTORE_FILE}" \
  -name nifi-root-ca \
  -passout "pass:${TRUSTSTORE_PASSWORD}"

echo
echo "TLS assets regenerated successfully:"
echo "  - ${CERT_FILE}"
echo "  - ${KEY_FILE}"
echo "  - ${KEYSTORE_FILE}"
echo "  - ${TRUSTSTORE_FILE}"
echo
echo "Next steps:"
echo "  1. docker compose restart nifi"
echo "  2. Re-open https://localhost:8443/nifi/ in the browser"
