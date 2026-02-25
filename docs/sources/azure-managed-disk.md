# Source: Azure Managed Disk

Creates a snapshot of an Azure managed disk using the Azure compute API.

**Module**: `backups.sources.azure_managed_disk`

## Example

```json
{
  "id": "mydisk1",
  "type": "azure-managed-disk",
  "name": "My Disk 1",
  "subscription_id": "285adaab-abcd-41cc-1234-9f256543d534",
  "source_resource_group": "MC_KUBERNETES_AZURECLUSTER1_NORTHEUROPE",
  "destination_resource_group": "MyBackupsResourceGroup",
  "disk_name": "mydisk1",
  "retain_snapshots": 3
}
```

## Parameters

| Key | Required | Purpose |
|-----|----------|---------|
| `id` | Yes | Unique identifier for this source. |
| `name` | No | Description for reporting (defaults to `id`). |
| `subscription_id` | Yes | Azure subscription ID. |
| `source_resource_group` | Yes | Resource group containing the managed disk. |
| `destination_resource_group` | Yes | Resource group where snapshots will be created. |
| `disk_name` | Yes | Name of the managed disk to snapshot. |
| `retain_snapshots` | No | Number of snapshots to retain on Azure. |

## Authentication

The following environment variables must be set (from an Azure AD service principal):

| Variable | Description |
|----------|-------------|
| `TENANT_ID` | Azure Tenant ID |
| `CLIENT_ID` | Azure client/app ID |
| `CLIENT_KEY` | Azure client secret key |
