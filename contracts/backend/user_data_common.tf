# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

locals {
  auths = {
    for registry in split(",", var.REGISTRY_URL):
      (registry) => {
        "username": var.REGISTRY_USERNAME,
        "password": var.REGISTRY_PASSWORD
      }
  }
  env = {
    "type" : "env",
    "logging" : {
      "syslog" : {
          "hostname" : var.SYSLOG_HOSTNAME,
          "port": var.SYSLOG_PORT,
          "server": var.SYSLOG_SERVER_CERT,
          "cert": var.SYSLOG_CLIENT_CERT,
          "key": var.SYSLOG_CLIENT_KEY,
      }
    },
    "volumes": {
      "vault_vol": {
          "seed": var.ENV_VOL_SEED,
      }
    },
    "auths": local.auths,
    "cacerts": length(var.REGISTRY_CA) > 0 ? [{certificate: var.REGISTRY_CA}] : [],
    "env" : {
        "PORT": var.PORT,
    }
  }
  workload_template = {
    "type" : "workload",
    "images": {},
    "volumes": {
        "vault_vol": {
            "filesystem": "ext4",
            "mount": "/mnt/data",
            "seed": var.WORKLOAD_VOL_SEED,
        }
    }
  }
}
