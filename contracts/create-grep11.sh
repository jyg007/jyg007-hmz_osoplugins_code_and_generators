#!/bin/bash

# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

if [ $# -ne 1 ]; then
  echo "Missing prefix argument"
  exit 1
fi

xorriso="/usr/bin/xorriso"

contract_root=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd "$contract_root"

pushd grep11
tofu init && tofu destroy -auto-approve && tofu apply -auto-approve
cp -rf grep11-c16.yml ../output/grep11/user-data
popd

pushd output/grep11
touch vendor-data
echo "local-hostname: $1-cs-backend-grep11" > meta-data
${xorriso} -as mkisofs -o cloud-init -V cidata -J -r user-data meta-data vendor-data
popd

popd

