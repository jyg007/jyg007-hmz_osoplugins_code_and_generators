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

contract_root=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

pushd "$contract_root"

pushd frontend_plugin
tofu init -upgrade && tofu destroy -auto-approve && tofu apply -auto-approve
cp frontend_plugin.yml ../output/frontend
popd

popd

