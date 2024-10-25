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

