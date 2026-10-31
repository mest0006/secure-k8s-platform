variable "name" {
  description = "Base name used for all resources."
  type        = string
}

variable "location" {
  description = "Azure region."
  type        = string
  default     = "canadacentral"
}

variable "kubernetes_version" {
  description = "AKS Kubernetes version. Null lets AKS pick the default supported version."
  type        = string
  default     = null
}

variable "node_vm_size" {
  description = "VM size for the system node pool."
  type        = string
  default     = "Standard_D4s_v5"
}

variable "node_min_count" {
  description = "Minimum nodes for the cluster autoscaler."
  type        = number
  default     = 2
}

variable "node_max_count" {
  description = "Maximum nodes for the cluster autoscaler."
  type        = number
  default     = 5
}

variable "admin_group_object_ids" {
  description = "Entra ID group object IDs granted cluster admin through Azure RBAC."
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "Tags applied to every resource."
  type        = map(string)
  default     = {}
}
