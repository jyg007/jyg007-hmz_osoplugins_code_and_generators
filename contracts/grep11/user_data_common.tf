# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

locals {
  auths = {
    (var.REGISTRY_URL) : {
      "username": var.REGISTRY_USERNAME,
      "password": var.REGISTRY_PASSWORD
    }
  }
  env = {
    "type" : "env",
    "cacerts": length(var.REGISTRY_CA) > 0 ? [{certificate: var.REGISTRY_CA}] : []
    "logging" : {
      "syslog" : {
          "hostname" : var.SYSLOG_HOSTNAME,
          "port": var.SYSLOG_PORT,
          "server": var.SYSLOG_SERVER_CERT,
          "cert": var.SYSLOG_CLIENT_CERT,
          "key": var.SYSLOG_CLIENT_KEY,
      }
    },
    "env" : {
      "PORT": var.PORT,
    }
  }
  workload_template = {
    "type" : "workload",
    "auths": local.auths,
    "images": {}
  }
}
