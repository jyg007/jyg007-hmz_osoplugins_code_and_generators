#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

variable "DEBUG" {
  type        = bool
  description = "Create debug contracts, plaintext"
  default     = false
}

variable "STANDALONE" {
  type        = bool
  description = "Create contract as standalone (enable bridge port and disable plugin)"
  default     = false
}

variable "SEED" {
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

variable "GREP11_ENDPOINT" {
  type = string
  description = "GREP11 backend endpoint (ex. <prefix>-cs-backend-grep11.control23.dap.local:9876)"
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

### Only required for stand-alone (without OSO) deployments ###

variable "ENV_VOL_SEED" {
  type = string
  description = "Environment volume encryption seed"
}

variable "REGISTRY_URL" {
  type        = string
  description = "Registry URL to pull an image"
}

variable "REGISTRY_USERNAME" {
  type        = string
  description = "Username to access your registry"
}

variable "REGISTRY_PASSWORD" {
  type        = string
  description = "Password to access your registry"
  sensitive   = true
}

variable "REGISTRY_CA" {
  type        = string
  description = "Registry certificate authority in base64 (optional for private registries)"
  default     = ""
}

variable "SYSLOG_HOSTNAME" {
  type        = string
  description = "Syslog server hostname"
}

variable "SYSLOG_PORT" {
  type        = number
  description = "Syslog server port number"
}

variable "SYSLOG_SERVER_CERT" {
  type        = string
  description = "Syslog server certificate"
}

variable "SYSLOG_CLIENT_CERT" {
  type        = string
  description = "Syslog server client certificate"
}

variable "SYSLOG_CLIENT_KEY" {
  type        = string
  sensitive   = true
  description = "Syslog server client key"
}

variable "PORT" {
  type        = string
  description = "External port number for api"
  default     = "4000"
}
