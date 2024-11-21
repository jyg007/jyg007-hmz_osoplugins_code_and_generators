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
}

variable "IMAGE" {
  type        = string
  description = "GREP11 image name with registry"
}

variable "PORT" {
  type        = string
  description = "GREP11 port number"
  default     = "9876"
}

variable "HPCR_CERT" {
  type        = string
  description = "Public HPCR certificate for contract encryption"
  nullable    = true
  default     = null
}

variable "DEBUG" {
  type        = bool
  description = "Create debug contracts, plaintext"
  default     = false
}

variable "DOMAIN" {
  type        =  string
  description = "Crypto appliance domain"
}

variable "C16_CLIENT_HOST" {
  type        = string
  default     = "192.168.7.4"
  description = "Crypto appliance host endpoint"
}

variable "C16_CLIENT_PORT" {
  type       = string
  default    = "9001"
}

variable "C16_CLIENT_LOGLEVEL" {
  type        = string
  default     = "debug"
  validation {
    condition     = contains(["trace", "debug", "info", "warn", "err", "error", "critical", "off"], var.C16_CLIENT_LOGLEVEL)
    error_message = "Valid values for var: C16_CLIENT_LOGLEVEL are (trace, debug, info, warn, err, error, critical, off)."
  }
}

variable "C16_CLIENT_KEY" {
  type        = string
  description = "Crypto appliance client key"
}

variable "C16_CLIENT_CERT" {
  type        = string
  description = "Crypto appliance client certificate"
}

variable "C16_CA_CERT" {
  type        = string
  description = "Crypto appliance CA certificate"
}

### Only required for stand-alone (without OSO) deployments ###

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

variable "CERT_VALIDITY_PERIOD" {
  type = string
  default = "720"
}
