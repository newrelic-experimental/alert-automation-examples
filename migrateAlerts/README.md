# Alert-Migration

New Relic Alerting Migration
===========================
Parses config file to get existing policies/conditions and creates them in a new account (alert migration). Currently handles APM/Infrastructure/Synthetics/NRQL conditions. Config file requires admin keys for original account and new account, as well as a list of policies names to migrate.

### Requirements

* Python 3+ & requests/yaml modules
* New Relic Account & valid admin API keys

## migration-config.yml
```
---
  admin_key: <key> #this is the originating account admin_key (where policies/conditions currently exist)
  new_admin_key: <key> #this is the admin key for the desired account to move policies/conditions to
  policyNames: ['pol1', 'pol2', 'pol3'] #this is a list of existing policies that will be moved to desired account
```

### NOTES
* When migrating APM conditions, entities will not automatically be assigned by default.
* Synthetic conditions will only be created if the monitor exists in the new (target) account. Otherwise, the condition(s) will be skipped during execution
* Plugin conditions require that the data is already reporting to the new account.
* If your policy name has an apostrophe or other character, use double quotes within the policyNames list instead
