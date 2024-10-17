#!/bin/bash

# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

contract_root=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd "$contract_root"

pushd frontend_plugin
tofu init -upgrade && tofu destroy -auto-approve && tofu apply -auto-approve
cp frontend_plugin.yml ../output/frontend
popd

popd

