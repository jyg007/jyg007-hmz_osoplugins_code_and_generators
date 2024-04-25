#!/bin/bash

COMPOSE=`tar -cz -C docker-compose/ . | base64 -w0` envsubst '\$COMPOSE' < vault.yml.tpl > vault.yml

WORKLOAD=`pwd`/vault.yml
CONTRACT_KEY=ibm-hyper-protect-container-runtime-23.6.2-encrypt.crt
PASSWORD=`openssl rand -base64 12`
ENCRYPTED_PASSWORD="$(echo -n "$PASSWORD" | base64 -d | openssl rsautl -encrypt -inkey $CONTRACT_KEY -certin | base64 -w0 )"
ENCRYPTED_WORKLOAD="$(echo -n "$PASSWORD" | base64 -d | openssl enc -aes-256-cbc -pbkdf2 -pass stdin -in "$WORKLOAD" | base64 -w0)"
echo "hyper-protect-basic.${ENCRYPTED_PASSWORD}.${ENCRYPTED_WORKLOAD}"
