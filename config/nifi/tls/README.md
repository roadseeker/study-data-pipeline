# config/nifi/tls

`config/nifi/tls` stores local-only TLS artifacts for Nexus Pay NiFi access.

- Generate the files on each PC with `bash scripts/nifi/regenerate_local_tls.sh`
- Keep generated `.pem` and `.p12` files out of Git
- Restart NiFi after regeneration so the container reloads the new keystore and truststore

Expected generated files:

- `localhost+2.pem`
- `localhost+2-key.pem`
- `nifi-keystore.p12`
- `nifi-truststore.p12`
