data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "this" {
  name     = "rg-${var.name}"
  location = var.location
  tags     = var.tags
}

resource "azurerm_log_analytics_workspace" "this" {
  name                = "log-${var.name}"
  location            = azurerm_resource_group.this.location
  resource_group_name = azurerm_resource_group.this.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

resource "azurerm_kubernetes_cluster" "this" {
  name                      = "aks-${var.name}"
  location                  = azurerm_resource_group.this.location
  resource_group_name       = azurerm_resource_group.this.name
  dns_prefix                = var.name
  kubernetes_version        = var.kubernetes_version
  sku_tier                  = "Standard"
  automatic_upgrade_channel = "patch"
  local_account_disabled    = true
  oidc_issuer_enabled       = true
  workload_identity_enabled = true
  azure_policy_enabled      = true
  tags                      = var.tags

  default_node_pool {
    name                         = "system"
    vm_size                      = var.node_vm_size
    auto_scaling_enabled         = true
    min_count                    = var.node_min_count
    max_count                    = var.node_max_count
    only_critical_addons_enabled = true
    zones                        = ["1", "2", "3"]

    upgrade_settings {
      max_surge = "33%"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  azure_active_directory_role_based_access_control {
    azure_rbac_enabled     = true
    admin_group_object_ids = var.admin_group_object_ids
  }

  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    network_policy      = "calico"
    load_balancer_sku   = "standard"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.this.id
  }

  key_vault_secrets_provider {
    secret_rotation_enabled = true
  }
}

resource "azurerm_key_vault" "this" {
  name                       = substr(replace("kv-${var.name}", "_", "-"), 0, 24)
  location                   = azurerm_resource_group.this.location
  resource_group_name        = azurerm_resource_group.this.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  enable_rbac_authorization  = true
  purge_protection_enabled   = true
  soft_delete_retention_days = 30
  tags                       = var.tags

  network_acls {
    default_action = "Deny"
    bypass         = "AzureServices"
  }
}

resource "azurerm_role_assignment" "csi_secrets_reader" {
  scope                = azurerm_key_vault.this.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_kubernetes_cluster.this.key_vault_secrets_provider[0].secret_identity[0].object_id
}
