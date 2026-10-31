terraform {
  required_version = ">= 1.6.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # Remote state with locking. Uncomment and point at your storage account.
  # backend "azurerm" {
  #   resource_group_name  = "rg-tfstate"
  #   storage_account_name = "sttfstate"
  #   container_name       = "tfstate"
  #   key                  = "secure-k8s-platform/dev.tfstate"
  # }
}

provider "azurerm" {
  features {}
}

module "aks" {
  source = "../../modules/aks"

  name           = "skp-dev"
  location       = "canadacentral"
  node_min_count = 2
  node_max_count = 4

  tags = {
    project     = "secure-k8s-platform"
    environment = "dev"
    managed_by  = "terraform"
  }
}

output "cluster_name" {
  value = module.aks.cluster_name
}
