# Script to automatically enable/disable alert policies (all conditions)
# Parameters: ENABLED = true/false // policies = pol1,pol2,pol3 // adminkey = <your_admin_key>
# Usage Example: ./alert-management.ps1 -ENABLED true -policies Keagan-Example,Keagan-Test,Lambda-Test -adminKey yzy34850
# Author: Keagan Peet

#Run arguments
param
(
    [Parameter(Mandatory)]
    [string]$ENABLED,
    [Parameter(Mandatory)]
    [string[]]$policies,
    [Parameter(Mandatory)]
    [string]$adminKey
)

$headers = @{
    "X-Api-Key" = $adminKey
}

$headers2 = @{
    "X-Api-Key" = $adminKey #IMPORTANT: POSTS/PUTS require admin key
    "Content-Type" = "application/json"
}

Function GetPolicyIDs(){
    $uri = "https://api.newrelic.com/v2/alerts_policies.json"
    $policyIDs = @()

    #get each policy ID for each policy name specified
    foreach ($name in $policies){
        $body = @{
            "filter[name]" = $name
        }
        try{
            $resp = Invoke-WebRequest -Uri $uri -Method GET -Headers $headers -Body $body
        } catch {$_.Exception.Response.StatusCode.Value__}
        $psObject = $resp | ConvertFrom-Json
        $policyIDs += $psObject.policies.id #store each policy id in an array to use later
    }
    return $policyIDs #return policy ID array
}

Function GetandUpdateConditions($ids) {
    $uri = "https://api.newrelic.com/v2/alerts_conditions.json"

    # get all conditions in a each policy by id
    foreach ($id in $ids){
        $body = @{
            "policy_id" = $id
        }
        try{
            $resp = Invoke-WebRequest -Uri $uri -Method GET -Headers $headers -Body $body
        } catch {$_.Exception.Response.StatusCode.Value__}
        $psObject = $resp | ConvertFrom-Json

        # modify all condition 'enabled' flags
        foreach ($obj in $psObject.conditions){
            $obj.enabled = $ENABLED #change flag
            $uri2 = "https://api.newrelic.com/v2/alerts_conditions/" + $obj.id + ".json" #place condition ID in PUT API endpoint
            Write-Host @("Updating APM Condition: " + [string]$obj.id)

            $obj.PSObject.Properties.Remove('id') #remove ID from payload (not required in PUT call)

            #convert obj back to json
            $body2 = @{
                condition = $obj
            } | ConvertTo-Json -Depth 3

            #update each condition with modified enabled flag
            try {
                $resp2 = Invoke-WebRequest -Uri $uri2 -Method Put -Headers $headers2 -Body $body2
            } catch {$_.Exception.Response.StatusCode.Value__}
        }
    }
}

Function GetandUpdateInfraConditions($ids) {
    foreach ($id in $ids){
        $uri = "https://infra-api.newrelic.com/v2/alerts/conditions?policy_id=" + [string]$id

        try{
            $resp = Invoke-WebRequest -Uri $uri -Method GET -Headers $headers #get all Infra conditions
        } catch {$_.Exception.Response.StatusCode.Value__}
        $psObject = $resp | ConvertFrom-Json

        if ($psObject.Data.Count -gt 0) { #if there are infra conditions in the policy, update them
            foreach ($obj in $psObject.data){ # modify all condition 'enabled' flags to false
                $uri2 = "https://infra-api.newrelic.com/v2/alerts/conditions/" + [string]$obj.id #place condition ID in PUT API endpoint

                $payload = @{
                    "enabled" = [System.Convert]::ToBoolean($ENABLED) #Infra alerts API requires a bool instead of string (string is accepted by regular alerts API)
                }

                #convert obj back to json
                $body = @{
                    data = $payload
                } | ConvertTo-Json

                Write-Host @("Updating Infrastructure Condition: " + [string]$obj.id)

                #update each condition with modified enabled flag
                try {
                    $resp2 = Invoke-WebRequest -Uri $uri2 -Method Put -Headers $headers2 -Body $body
                } catch {$_.Exception.Response.StatusCode.Value__}
            }
        }
    }
}

Function GetAndUpdateNRQLConditions($ids) {
  #For each policy id, get nrql conditions
  foreach ($id in $ids) {
    $body = @{
        "policy_id" = $id
    }
    $uri = "https://api.newrelic.com/v2/alerts_nrql_conditions.json"

    try{
      $resp = Invoke-WebRequest -Uri $uri -Method GET -Headers $headers -Body $body #get all NRQL conditions
    } catch {$_.Exception.Response.StatusCode.Value__}
    $psObject = $resp | ConvertFrom-Json

    if ($psObject.nrql_conditions.Count -gt 0) { #if there are nrql conditions in response
      foreach ($obj in $psObject.nrql_conditions) {
        $uri2 = "https://api.newrelic.com/v2/alerts_nrql_conditions/" + [string]$obj.id + ".json" #put endpoint
        $obj.enabled = $ENABLED
        Write-Host @("Updating NRQL Condition: " + [string]$obj.id)

        $obj.PSObject.Properties.Remove('id') #remove ID from payload (not required in PUT call)

        #convert obj back to json
        $body2 = @{
            nrql_condition = $obj
        } | ConvertTo-Json -Depth 4

        #update each condition with modified enabled flag
        try {
            $resp2 = Invoke-WebRequest -Uri $uri2 -Method Put -Headers $headers2 -Body $body2
        } catch {$_.Exception.Response.StatusCode.Value__}
      }
    }
  }
}

Function GetAndUpdateSyntheticConditions($ids) {
  foreach ($id in $ids) {
    $body = @{
        "policy_id" = $id
    }
    $uri = "https://api.newrelic.com/v2/alerts_synthetics_conditions.json"

    try{
      $resp = Invoke-WebRequest -Uri $uri -Method GET -Headers $headers -Body $body #get all synthetic conditions
    } catch {$_.Exception.Response.StatusCode.Value__}
    $psObject = $resp | ConvertFrom-Json

    if ($psObject.synthetics_conditions.Count -gt 0) {
      foreach ($obj in $psObject.synthetics_conditions) {
        $uri2 = "https://api.newrelic.com/v2/alerts_synthetics_conditions/" + [string]$obj.id + ".json"
        $obj.enabled = $ENABLED
        Write-Host @("Updating Synthetic Condition: " + [string]$obj.id)

        $obj.PSObject.Properties.Remove('id') #remove ID from payload (not required in PUT call)

        #convert obj back to json
        $body2 = @{
            synthetics_condition = $obj
        } | ConvertTo-Json -Depth 2

        #update each condition with modified enabled flag
        try {
            $resp2 = Invoke-WebRequest -Uri $uri2 -Method Put -Headers $headers2 -Body $body2
        } catch {$_.Exception.Response.StatusCode.Value__}
      }
    }
  }
}

Function Main() {
  $polIds = GetPolicyIDs
  GetandUpdateConditions($polIds)
  GetandUpdateInfraConditions($polIds)
  GetAndUpdateNRQLConditions($polIds)
  GetAndUpdateSyntheticConditions($polIds)

  Write-Host "Complete!"
}

Main
