#!/bin/sh
set -e

set_property() {
  key="$1"
  value="$2"
  file="/opt/nifi/nifi-current/conf/nifi.properties"

  if grep -q "^${key}=" "$file"; then
    sed -i "s#^${key}=.*#${key}=${value}#" "$file"
  else
    printf '\n%s=%s\n' "$key" "$value" >> "$file"
  fi
}

# If trusted localhost certificates are provided, wire them into NiFi's conf dir
# before delegating to the official startup script.
if [ -f /opt/nifi/custom-config/tls/nifi-keystore.p12 ] && [ -f /opt/nifi/custom-config/tls/nifi-truststore.p12 ]; then
  cp /opt/nifi/custom-config/tls/nifi-keystore.p12 /opt/nifi/nifi-current/conf/keystore.p12
  cp /opt/nifi/custom-config/tls/nifi-truststore.p12 /opt/nifi/nifi-current/conf/truststore.p12

  set_property "nifi.security.keystore" "./conf/keystore.p12"
  set_property "nifi.security.keystoreType" "PKCS12"
  set_property "nifi.security.keystorePasswd" "changeit"
  set_property "nifi.security.keyPasswd" "changeit"
  set_property "nifi.security.truststore" "./conf/truststore.p12"
  set_property "nifi.security.truststoreType" "PKCS12"
  set_property "nifi.security.truststorePasswd" "changeit"
  set_property "nifi.security.needClientAuth" "false"
fi

if [ -n "${SINGLE_USER_CREDENTIALS_USERNAME:-}" ] && [ -n "${SINGLE_USER_CREDENTIALS_PASSWORD:-}" ]; then
  /opt/nifi/nifi-current/bin/nifi.sh set-single-user-credentials \
    "${SINGLE_USER_CREDENTIALS_USERNAME}" \
    "${SINGLE_USER_CREDENTIALS_PASSWORD}"
fi

exec /opt/nifi/scripts/start.sh
