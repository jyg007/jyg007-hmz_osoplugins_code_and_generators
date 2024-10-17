#!/bin/bash

# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

xorriso="/usr/bin/xorriso"

contract_root=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd "$contract_root"

pushd backend
tofu init && tofu destroy -auto-approve && tofu apply -auto-approve
cp -rf backend.yml ../output/backend/user-data
popd

pushd output/backend
touch vendor-data
echo "local-hostname: backend" > meta-data
${xorriso} -as mkisofs -o cloud-init -V cidata -J -r user-data meta-data vendor-data
cloud-localds cloud-init -V vendor-data user-data meta-data
popd

popd

