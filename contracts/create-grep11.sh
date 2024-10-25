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

