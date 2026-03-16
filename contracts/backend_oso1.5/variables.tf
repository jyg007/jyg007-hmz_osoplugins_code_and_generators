#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

variable "PREFIX" {
  type        = string
  default = ""
}

variable "DEBUG" {
  type        = bool
  description = "Create debug contracts, plaintext"
  default     = false
}

variable "OSOENCRYPTIONPASS" {
  type        = string
  description = "Encrypt data through the iteration pipeline (should be the same value as frontend plugin)"
  default     = ""
}

variable "BACKEND_PLUGIN_IMAGE" {
  type = string
  description = "Backend plugin image containing registry"
}

variable "COLD_BRIDGE_IMAGE" {
  type = string
  description = "Cold bridge image containing registry"
}

variable "COLD_VAULT_IMAGE" {
  type = string
  description = "Cold vault image containing registry"
}

variable "KMSCONNECT_IMAGE" {
  type = string
  description = "KMS connect image containing registry"
}

variable "GREP11_IMAGE" {
  type = string
  description = "IBM Grep11 image containing registry"
}

variable "NGINX_IMAGE" {
  type = string
  description = "nginx image containing registry"
}

variable "VAULT_ID" {
  type = string
  description = "Vault ID"
}

variable "PASSPHRASE" {
  type = string
  default = "{{EMPTY}}"
  description = "Required to enable plugin to view content within a JSON format"
}

variable "NOTARY_MESSAGING_PUBLIC_KEY" {
  type = string
  description = "Notary messaging public key after performing genesis"
}

variable "HPCR_CERT" {
  type        = string
  description = "Public HPCR certificate for contract encryption"
  nullable    = true
  default     = null
}

variable "GREP11_HOST" {
  type = string
  description = "GREP11 backend endpoint"
  #  default = "192.168.96.21"
  default = "localhost"
}

variable "GREP11_PORT" {
  type = string
  description = "GREP11 backend endpoint port"
  default = "9876"
}

variable "GREP11_CA" {
  type = string
  description = "GREP11 CA certificate"
}

variable "GREP11_CLIENT_KEY" {
  type = string
  description = "GREP11 client key"
}

variable "GREP11_CLIENT_CERT" {
  type = string
  description = "GREP11 client certificate"
}

variable "WORKLOAD_VOL_SEED" {
  type = string
  description = "Workload volume encryption seed"
}

variable "PORT" {
  type        = string
  description = "External port number for api"
  default     = "4000"
}

variable "STATIC_IP" {
  type        = bool
  description = "Deploying via OSO release that supports static IP"
  default     = true
}
