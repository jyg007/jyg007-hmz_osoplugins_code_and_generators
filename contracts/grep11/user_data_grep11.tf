#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

resource "local_file" "grep11_cfg" {
  content = local.grep11_cfg
  filename = "docker-compose/srv1/grep11server.yaml"
  file_permission = "0664"
}

resource "local_file" "grep11_ca_cert" {
  content = tls_self_signed_cert.grep11_ca_cert.cert_pem
  filename = "docker-compose/srv1/grep11ca.pem"
  file_permission = "0664"
}

resource "local_file" "grep11_server_key" {
  content = tls_private_key.server_key.private_key_pem
  filename = "docker-compose/srv1/grep11server-key.pem"
  file_permission = "0664"
}

resource "local_file" "grep11_server_cert" {
  content = tls_locally_signed_cert.server_cert.cert_pem
  filename = "docker-compose/srv1/grep11server.pem"
  file_permission = "0664"
}

resource "local_file" "c16_client_cfg" {
  content = local.c16_cfg
  filename = "docker-compose/cfg/c16client.yaml"
  file_permission = "0664"
}

resource "local_file" "c16_ca_cert" {
  content = var.C16_CA_CERT
  filename = "docker-compose/cfg/ca.pem"
  file_permission = "0664"
}

resource "local_file" "c16_client_cert" {
  content = var.C16_CLIENT_CERT
  filename = "docker-compose/cfg/c16client.pem"
  file_permission = "0664"
}

resource "local_file" "c16_client_key" {
  content = var.C16_CLIENT_KEY
  filename = "docker-compose/cfg/c16client-key.pem"
  file_permission = "0664"
}

resource "local_file" "docker_compose" {
  content = templatefile(
    "${path.module}/grep11-c16.yml.tftpl",
    { tpl = {
      image = var.IMAGE,
      PORT = var.PORT
    } },
  )
  filename = "docker-compose/docker-compose.yml"
  file_permission = "0664"

  depends_on = [
    local_file.grep11_cfg,
    local_file.grep11_ca_cert,
    local_file.grep11_server_key,
    local_file.grep11_server_cert,
    local_file.c16_client_cfg,
    local_file.c16_ca_cert,
    local_file.c16_client_cert,
    local_file.c16_client_key
  ]
}

# archive of the folder containing docker-compose file. This folder could create additional resources such as files
# to be mounted into containers, environment files etc. This is why all of these files get bundled in a tgz file (base64 encoded)
resource "hpcr_tgz" "workload" {
  depends_on = [ local_file.docker_compose ]
  folder = "docker-compose"
}


locals {
  c16_cfg = <<-EOT
    loglevel: ${var.C16_CLIENT_LOGLEVEL}
    servers:
      - hostname: ${var.C16_CLIENT_HOST}
        port: ${var.C16_CLIENT_PORT}
        mTLS: true
        server_cert_file: "/etc/c16/ca.pem"
        client_key_file: "/etc/c16/c16client-key.pem"
        client_cert_file: "/etc/c16/c16client.pem"
  EOT
  grep11_cfg = <<-EOT
    logging:
      levels:
        entry: debug
    ep11crypto:
      enabled: true
      connection:
        address: 0.0.0.0
        port: 9876
        tls:
          enabled: true
          certfile: /cfg/grep11server.pem
          keyfile: /cfg/grep11server-key.pem
          mutual: true
          cacert: /cfg/grep11ca.pem
          cacertbytes:
          certfilebytes:
          keyfilebytes:
        keepalive:
          serverKeepaliveTime: 30
          serverKeepaliveTimeout: 5
      domain: "${var.DOMAIN}"
  EOT
  compose = {
    "compose" : {
      "archive" : hpcr_tgz.workload.rendered
    }
  }
  workload = merge(local.workload_template, local.compose)
  contract = yamlencode({
    "env" : local.env,
    "workload" : local.workload
  })
}

# In this step we encrypt the fields of the contract and sign the env and workload field. The certificate to execute the
# encryption it built into the provider and matches the latest HPCR image. If required it can be overridden.
# We use a temporary, random keypair to execute the signature. This could also be overriden.
resource "hpcr_contract_encrypted" "contract" {
  contract  = local.contract
  cert      = var.HPCR_CERT == "" ? null : var.HPCR_CERT
}

resource "local_file" "contract" {
  count    = var.DEBUG ? 1 : 0
  content  = yamlencode(local.contract)
  filename = "grep11-c16_plain.yml"
  file_permission = "0664"
}

resource "local_file" "contract_encrypted" {
  content  = hpcr_contract_encrypted.contract.rendered
  filename = "grep11-c16.yml"
  file_permission = "0664"
}
