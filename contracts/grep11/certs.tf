#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

# org ca cert used to sign everything
resource "tls_private_key" "grep11_ca_private_key" {
  algorithm = "RSA"
}

resource "tls_self_signed_cert" "grep11_ca_cert" {
  private_key_pem = tls_private_key.grep11_ca_private_key.private_key_pem

  is_ca_certificate = true

  subject {
    common_name         = "dap.local"
    country             = "US"
    organization        = "HPS"
  }

  validity_period_hours = var.CERT_VALIDITY_PERIOD

  allowed_uses = [
    "digital_signature",
    "cert_signing",
    "crl_signing",
  ]
}

resource "local_file" "ca_cert" {
    content  = tls_self_signed_cert.grep11_ca_cert.cert_pem
    filename = "./certs/grep11ca.pem"
}

resource "local_file" "ca_key" {
    content = tls_private_key.grep11_ca_private_key.private_key_pem
    filename = "./certs/grep11ca-key.pem"
}

resource "tls_private_key" "server_key" {
  algorithm = "RSA"
}

resource "tls_cert_request" "server_cert" {
  private_key_pem = tls_private_key.server_key.private_key_pem

  dns_names = [format("%s-cs-backend-grep11.control23.dap.local:%s", var.PREFIX, var.PORT), format("%s-cs-backend-grep11.control23.dap.local", var.PREFIX)]

  ip_addresses = var.STATIC_IP ? [for ip in var.STATIC_IP_ADDRS : ip if length(ip) > 0] : null

  subject {
    common_name  = "grep11-c16.control23.dap.local"
    organization = "HPS"
    country      = "US"
  }
}

resource "tls_locally_signed_cert" "server_cert" {
  // CA certificate for product
  ca_cert_pem = tls_self_signed_cert.grep11_ca_cert.cert_pem

  // CSR for service
  cert_request_pem = tls_cert_request.server_cert.cert_request_pem
  // CA Private key for service
  ca_private_key_pem = tls_private_key.grep11_ca_private_key.private_key_pem

  validity_period_hours = var.CERT_VALIDITY_PERIOD

  allowed_uses = [
    "digital_signature",
    "key_encipherment",
    "server_auth",
  ]
}

resource "local_file" "server_key" {
  content  = tls_private_key.server_key.private_key_pem
  filename = "./certs/grep11server-key.pem"
  file_permission = 0660
}

resource "local_file" "server_cert" {
  content  = tls_locally_signed_cert.server_cert.cert_pem
  filename = "./certs/grep11server.pem"
  file_permission = 0660
}

resource "tls_private_key" "client_key" {
  algorithm = "RSA"
}

resource "tls_cert_request" "client_cert" {
  private_key_pem = tls_private_key.client_key.private_key_pem

  subject {
    common_name  = "client"
    organization = "HPS"
    country      = "US"
  }
}

resource "tls_locally_signed_cert" "client_cert" {
  // CA certificate for product
  ca_cert_pem = tls_self_signed_cert.grep11_ca_cert.cert_pem

  // CSR for service
  cert_request_pem = tls_cert_request.client_cert.cert_request_pem
  // CA Private key for service
  ca_private_key_pem = tls_private_key.grep11_ca_private_key.private_key_pem

  validity_period_hours = var.CERT_VALIDITY_PERIOD

  allowed_uses = [
    "digital_signature",
    "key_encipherment",
    "client_auth",
  ]
}

resource "local_file" "client_key" {
  content  = tls_private_key.client_key.private_key_pem
  filename = "./certs/grep11client-key.pem"
  file_permission = 0660
}

resource "local_file" "client_cert" {
  content  = tls_locally_signed_cert.client_cert.cert_pem
  filename = "./certs/grep11client.pem"
  file_permission = 0660
}
