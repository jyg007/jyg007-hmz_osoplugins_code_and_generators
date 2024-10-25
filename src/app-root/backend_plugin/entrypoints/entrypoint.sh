#!/bin/bash
#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#
#

mkdir -p /app-root/all-certs

# Write certs to file
echo "${COMPONENT_CA_CERT}" >/app-root/all-certs/component-ca-cert.pem
echo "${BACKEND_CERT}" >/app-root/all-certs/backend-certificate.pem
echo "${BACKEND_KEY}" >/app-root/all-certs/backend-key.pem

export COMPONENT_FINGERPRINTS="${BRIDGE_FINGERPRINT}"

unset CONF_FILE
CONF_FILE=/app-root/entrypoints/supervisord-backend_plugin.conf

cd /app-root/entrypoints || exit

SUPERVISORD_CONF=/usr/local/etc/supervisord.conf
cp ${CONF_FILE} ${SUPERVISORD_CONF}
supervisord -c ${SUPERVISORD_CONF}
