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

FRONTEND_PLUGIN_FILE="./output/frontend/frontend_plugin.yml"
if [ ! -f $FRONTEND_PLUGIN_FILE ]; then
  echo "frontend plugin file does not exist: $FRONTEND_PLUGIN_FILE"
  exit 1
fi
FRONTEND_PLUGIN=$(cat "$FRONTEND_PLUGIN_FILE")

BACKEND_FILE="./output/backend/user-data"
if [ ! -f $BACKEND_FILE ]; then
  echo "backend file does not exist: $BACKEND_FILE"
  exit 1
fi
BACKEND=$(cat "$BACKEND_FILE")

GREP11_FILE="./output/grep11/user-data"
if [ ! -f $GREP11_FILE ]; then
  echo "backend file does not exist: $GREP11_FILE"
#  exit 1
fi
GREP11=$(cat "$GREP11_FILE")

cat <<-EOT
# Hyper Protect Encrypted Workloads
FRONTEND_WORKLOADS=[
  {
    persistent_vol: null,
    name: "frontend-plugin",
    workload: "$FRONTEND_PLUGIN"
  }
]

BACKEND_WORKLOADS=[
  {
    name: "backend-plugin",
    hipersocket34: false,
    workload: "$BACKEND",
    persistent_vol: {
      volume_name = "vault_vol",
      env_seed = "vaultseed2",
      prev_seed = "",
      volume_path = "/var/lib/libvirt/images/oso/vault-data.qcow2"
    }
  },
  {
    persistent_vol: null,
    name: "backend-grep11",
    hipersocket34: true,
    workload: "$GREP11"
  }
]
EOT
