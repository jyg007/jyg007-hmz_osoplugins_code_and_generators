#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

resource "local_file" "frontend_plugin_docker_compose" {
  content = templatefile(
    "${path.module}/frontend_plugin.yml.tftpl",
    { tpl = {
      image = var.FRONTEND_PLUGIN_IMAGE,
      SK = var.SK,
      VAULTID = var.VAULT_ID,
      HMZ_SERVER = var.HMZ_SERVER,
      ROOTCERT = var.ROOTCERT,
      SEED = var.SEED,
    } },
  )
  filename = "frontend_plugin/docker-compose.yml"
  file_permission = "0664"
}

# archive of the folder containing docker-compose file. This folder could create additional resources such as files
# to be mounted into containers, environment files etc. This is why all of these files get bundled in a tgz file (base64 encoded)
resource "hpcr_tgz" "frontend_plugin_workload" {
  depends_on = [ local_file.frontend_plugin_docker_compose ]
  folder = "frontend_plugin"
}


locals {
  frontend_plugin_compose = {
    "compose" : {
      "archive" : hpcr_tgz.frontend_plugin_workload.rendered
    }
  }
  frontend_plugin_workload = merge(local.workload_template, local.frontend_plugin_compose)
}

# In this step we encrypt the fields of the contract and sign the env and workload field. The certificate to execute the
# encryption it built into the provider and matches the latest HPCR image. If required it can be overridden.
# We use a temporary, random keypair to execute the signature. This could also be overriden.
resource "hpcr_text_encrypted" "frontend_plugin_contract" {
  text      = yamlencode(local.frontend_plugin_workload)
  cert      = var.HPCR_CERT == "" ? null : var.HPCR_CERT
}

resource "local_file" "frontend_plugin_contract" {
  count    = var.DEBUG ? 1 : 0
  content  = yamlencode(local.frontend_plugin_workload)
  filename = "frontend_plugin_contract.yml"
  file_permission = "0664"
}

resource "local_file" "frontend_plugin_contract_encrypted" {
  content  = hpcr_text_encrypted.frontend_plugin_contract.rendered
  filename = "frontend_plugin.yml"
  file_permission = "0664"
}
