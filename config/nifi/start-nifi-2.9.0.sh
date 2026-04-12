#!/bin/sh
set -e

# If trusted localhost certificates are provided, wire them into NiFi's conf dir
# before delegating to the official startup script.
if [ -f /opt/nifi/custom-config/tls/nifi-keystore.p12 ] && [ -f /opt/nifi/custom-config/tls/nifi-truststore.p12 ]; then
  cp /opt/nifi/custom-config/tls/nifi-keystore.p12 /opt/nifi/nifi-current/conf/keystore.p12
  cp /opt/nifi/custom-config/tls/nifi-truststore.p12 /opt/nifi/nifi-current/conf/truststore.p12

  sed -i 's#^nifi.security.keystore=.*#nifi.security.keystore=./conf/keystore.p12#' /opt/nifi/nifi-current/conf/nifi.properties
  sed -i 's#^nifi.security.keystoreType=.*#nifi.security.keystoreType=PKCS12#' /opt/nifi/nifi-current/conf/nifi.properties
  sed -i 's#^nifi.security.keystorePasswd=.*#nifi.security.keystorePasswd=changeit#' /opt/nifi/nifi-current/conf/nifi.properties
  sed -i 's#^nifi.security.keyPasswd=.*#nifi.security.keyPasswd=changeit#' /opt/nifi/nifi-current/conf/nifi.properties
  sed -i 's#^nifi.security.truststore=.*#nifi.security.truststore=./conf/truststore.p12#' /opt/nifi/nifi-current/conf/nifi.properties
  sed -i 's#^nifi.security.truststoreType=.*#nifi.security.truststoreType=PKCS12#' /opt/nifi/nifi-current/conf/nifi.properties
  sed -i 's#^nifi.security.truststorePasswd=.*#nifi.security.truststorePasswd=changeit#' /opt/nifi/nifi-current/conf/nifi.properties
  sed -i 's#^nifi.security.needClientAuth=.*#nifi.security.needClientAuth=false#' /opt/nifi/nifi-current/conf/nifi.properties
fi

if [ -n "${SINGLE_USER_CREDENTIALS_USERNAME:-}" ] && [ -n "${SINGLE_USER_CREDENTIALS_PASSWORD:-}" ]; then
  /opt/nifi/nifi-current/bin/nifi.sh set-single-user-credentials \
    "${SINGLE_USER_CREDENTIALS_USERNAME}" \
    "${SINGLE_USER_CREDENTIALS_PASSWORD}"
fi

exec /opt/nifi/scripts/start.sh
