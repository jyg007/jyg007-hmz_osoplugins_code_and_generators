#!/bin/bash

# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

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
