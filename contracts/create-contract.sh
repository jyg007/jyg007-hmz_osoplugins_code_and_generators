#!/bin/bash

# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

contract_root=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd "$contract_root"
pushd backend_sidecar
terraform init -upgrade && terraform destroy -auto-approve && terraform apply -auto-approve
cp backend_sidecar.yml ../user_data/backend
popd

pushd frontend_sidecar
terraform init -upgrade && terraform destroy -auto-approve && terraform apply -auto-approve
cp frontend_sidecar.yml ../user_data/frontend
popd

popd
