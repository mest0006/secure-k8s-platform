# Security notes

## Controls in this repo

| Layer | Control |
|---|---|
| Source | gitleaks secret scanning on every push and PR |
| Build | Trivy image scan; fixable HIGH/CRITICAL fails the build |
| Image | Distroless, non-root, no shell; deployed by digest |
| Admission | Kyverno: no `:latest`, non-root, no privilege escalation, capabilities dropped, read-only root FS, requests and limits, allowed registries only |
| Runtime | seccomp RuntimeDefault, no service account token mounted, default-deny NetworkPolicy |
| Cloud | AKS with Entra ID + Azure RBAC, local accounts disabled, workload identity, Azure Policy, Key Vault with RBAC, purge protection and network ACLs |
| IaC | Checkov scan of Terraform (report-only) |

## Known Checkov findings (accepted for a reference project)

- **Private API server not enabled.** A production cluster would use a private API endpoint or authorized IP ranges; left public so the reference can be created without a VPN or jump host.
- **No customer-managed keys for disk encryption.** Platform-managed keys are used to keep the example self-contained.
- **Key Vault without private endpoint.** Network ACLs deny by default; a private endpoint would be added with the cluster's virtual network.
