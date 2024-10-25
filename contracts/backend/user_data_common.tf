#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

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
