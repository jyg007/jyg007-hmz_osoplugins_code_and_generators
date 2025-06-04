#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

resource "local_file" "ibm_cfg" {
  content = local.ibm_cfg
  filename = "docker-compose/ibm.cfg"
  file_permission = "0664"
}

resource "local_file" "grep_ca" {
  content = var.GREP11_CA
  filename = "docker-compose/cert/ca.pem"
  file_permission = "0664"
}

resource "local_file" "grep_client_key" {
  content = var.GREP11_CLIENT_KEY
  filename = "docker-compose/cert/client-key.pem"
  file_permission = "0664"
}

resource "local_file" "grep_client_cert" {
  content = var.GREP11_CLIENT_CERT
  filename = "docker-compose/cert/client.pem"
  file_permission = "0664"
}

resource "local_file" "docker_compose" {
  content = templatefile(
    "${path.module}/backend.yml.tftpl",
    { tpl = {
      backend_plugin_image = var.BACKEND_PLUGIN_IMAGE,
      cold_bridge_image = var.COLD_BRIDGE_IMAGE,
      cold_vault_image = var.COLD_VAULT_IMAGE,
      kmsconnect_image = var.KMSCONNECT_IMAGE,
      vault_id = var.VAULT_ID,
      passphrase = var.PASSPHRASE,
      notary_messaging_public_key = var.NOTARY_MESSAGING_PUBLIC_KEY,
      seed = var.SEED,
    } },
  )
  filename = "docker-compose/docker-compose.yml"
  file_permission = "0664"

  depends_on = [
    local_file.ibm_cfg,
    local_file.grep_ca,
    local_file.grep_client_key,
    local_file.grep_client_cert
  ]
}


# archive of the folder containing docker-compose file. This folder could create additional resources such as files
# to be mounted into containers, environment files etc. This is why all of these files get bundled in a tgz file (base64 encoded)
resource "hpcr_tgz" "workload" {
  depends_on = [ local_file.docker_compose ]
  folder = "docker-compose"
}

locals {
  grep11_endpoint = var.STATIC_IP ? format("%s:%s", var.GREP11_HOST, var.GREP11_PORT): format("%s-cs-backend-grep11.control23.dap.local:%s", var.PREFIX, var.GREP11_PORT)
  ibm_cfg = <<-EOT
    system = onprem
    endpoint = ${local.grep11_endpoint}
  EOT
  compose = {
    "compose" : {
      "archive" : hpcr_tgz.workload.rendered
    }
  }
  workload = merge(local.workload_template, local.compose)
}

# In this step we encrypt the fields of the contract and sign the env and workload field. The certificate to execute the
# encryption it built into the provider and matches the latest HPCR image. If required it can be overridden.
# We use a temporary, random keypair to execute the signature. This could also be overriden.
resource "hpcr_text_encrypted" "contract" {
  text      = yamlencode(local.workload)
  cert      = var.HPCR_CERT == "" ? null : var.HPCR_CERT
}

resource "local_file" "contract" {
  count    = var.DEBUG ? 1 : 0
  content  = yamlencode(local.workload)
  filename = "backend_plain.yml"
  file_permission = "0664"
}

resource "local_file" "contract_encrypted" {
  content  = hpcr_text_encrypted.contract.rendered
  filename = "backend.yml"
  file_permission = "0664"
}
