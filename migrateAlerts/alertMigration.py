#!usr/bin/python

#########################################################################################################
# Author: Keagan Peet
# Purpose: To migrate all desired policies/conditions for a given account to another account.
# Note: Using python 3
# Usage: python3 alertMigration.py
#########################################################################################################

import json
import requests
import yaml

# You do not need to have entities reporting for infra conditions, filter clauses will pick up after entities start reporting.
# Creation of apm conditions will not have any entities assigned, this must be done later manually.

global infra_post_api
infra_post_api = 'https://infra-api.newrelic.com/v2/alerts/conditions'

def getPolicy(pol):
    headerz = {'X-Api-Key': str(admin_key)}
    policy_api = 'https://api.newrelic.com/v2/alerts_policies.json'
    print("Getting Existing Alert Policy: " + str(pol))
    payload = {'filter[name]': pol }
    r = requests.get(policy_api, headers=headerz, params=payload)
    if r.status_code == 200:
        response = r.json()
        foundName = False
        n = 0
        while foundName is False: #filter can return multiple policies if name string is a substring of multiple policies
            if response['policies'][n]['name'] == pol: #if exact name match, get the id
                id = response['policies'][n]['id']
                ip = response['policies'][n]['incident_preference']
                foundName = True
            else: #otherwise continue search
                n += 1
        return id, ip
    else:
        print ("Error! Status code: " + str(r.status_code))
        print(r.content)

def getInfraConditions(pID):
    headerz = {'X-Api-Key': str(admin_key)}
    infra_api = 'https://infra-api.newrelic.com/v2/alerts/conditions?policy_id=' + str(pID) #+ '&offset=50&list=10'
    r = requests.get(infra_api, headers=headerz)
    if str(r.status_code)[:1] == '2':
        conds = r.json() # all conditions initially
        return conds
    else:
        print("Failed with status code: " + str(r.status_code))
        print(r.content)


def getSyntheticConditions(pID):
    headerz = {'X-Api-Key': str(admin_key)}
    syn_api = 'https://api.newrelic.com/v2/alerts_synthetics_conditions.json'
    body = {'policy_id': pID}
    r = requests.get(syn_api, headers=headerz, params=body)
    if (str(r.status_code)[:1] == '2'):
        conds = r.json()
        return conds
    else:
        print("Failed with status code: " + str(r.status_code))
        print(r.content)

def getExistingMonitorName(id):
    headerz = {'X-Api-Key': str(admin_key)}
    api = 'https://synthetics.newrelic.com/synthetics/api/v3/monitors/' + id
    r = requests.get(api, headers=headerz)
    if (str(r.status_code)[:1] == '2'):
        existingMonitor = r.json()
        return existingMonitor['name']
    else:
        print("Failed with status code: " + str(r.status_code))
        print(r.content)

def getNewMonitorId(name):
    api = 'https://api.newrelic.com/graphql'
    h = {'API-Key': new_graph_key, 'Content-Type': 'application/json'}
    vars = {"entitySearchQuery":  "domain in ('SYNTH') and name='" + name + "' and tags.accountId=" + new_account_id}
    query = '''
      query($entitySearchQuery: String) {
        actor {
          entitySearch(query: $entitySearchQuery) {
            results {
              entities {
                ... on SyntheticMonitorEntityOutline {
                  name
                  monitorId
                }
              }
            }
          }
        }
      }
    '''

    r = requests.post(api, headers=h, json={'query': query, 'variables': vars})
    resp = r.json()
    if (r.status_code == 200):
        if (len(resp['data']['actor']['entitySearch']['results']['entities']) > 0):
            monitorId = resp['data']['actor']['entitySearch']['results']['entities'][0]['monitorId']
            return monitorId
        else:
            print("No matching id found for monitor: " + name + ' within target account. Skipping...')

        return 'none'

def getNRQLConditions(pID):
    page = 1
    tryAgain = True
    headerz = {'X-Api-Key': str(admin_key)}
    nrql_api = 'https://api.newrelic.com/v2/alerts_nrql_conditions.json'
    allConds = {'nrql_conditions': []}
    try:
        while (tryAgain):
            body = {'policy_id': pID, 'page': page}
            r = requests.get(nrql_api, headers=headerz,params=body)
            if str(r.status_code)[:1] == '2':
                conds = r.json()
                for cond in conds['nrql_conditions']:
                    allConds['nrql_conditions'].append(cond)
                page += 1
                if 'last' not in r.links:
                    tryAgain = False
            else:
                print("Failed with status code: " + str(r.status_code))
        return allConds
    except IndexError:
        return 'IndexError'

def getAPMConditions(pID):
    apm_api = 'https://api.newrelic.com/v2/alerts_conditions.json'
    headerz = {'X-Api-Key': str(admin_key)}
    body = {'policy_id': pID}
    r = requests.get(apm_api, headers=headerz, params=body)
    if str(r.status_code)[:1] == '2':
        conds = r.json()
        return conds
    else:
        print("Failed with status code: " + str(r.status_code))
        print(r.content)


def getSynConditions(pID):
    headerz = {'X-API-Key': str(admin_key)}
    syn_api = 'https://api.newrelic.com/v2/alerts_synthetics_conditions.json'
    body = {'policy_id': pID}
    r = requests.get(syn_api, headers=headerz, params=body)
    if str(r.status_code)[:1]== '2':
        conds = r.json()
        return conds
    else:
        print("Failed with status code: " + str(r.status_code))
        print(r.content)


def getPluginConditions(pID):
    headerz = {'X-API-Key': str(admin_key)}
    plugin_api = 'https://api.newrelic.com/v2/alerts_plugins_conditions.json'
    body = {'policy_id': pID}
    r = requests.get(plugin_api, headers=headerz, params=body)
    if str(r.status_code)[:1] == '2':
        conds = r.json();
        return conds
    else:
        print("Failed with status code: " + str(r.status_code))
        print(r.content)


def postInfraConditionsToNewAccount(newPolId, conds):
    for cond in conds['data']:
        type = cond['type']
        if type == 'infra_process_running':
            iName = cond['name']
            iFilter = ""
            if 'filter' in cond:
                iFilter = cond['filter']
            iCompare = cond['comparison']
            iCrit = cond['critical_threshold']['value']
            iCritD = cond['critical_threshold']['duration_minutes']
            iProc = ""
            if 'process_filter' in cond:
                iProc = cond['process_filter']
            createProcessNotRunning(type, iName, iFilter, newPolId, iCompare, iCrit, iCritD, iProc)
        elif type == 'infra_host_not_reporting':
            hName = cond['name']
            hFilter = ""
            if 'filter' in cond:
                hFilter = cond['filter']
            hCritD = cond['critical_threshold']['duration_minutes']
            createHostNotReporting(type, hName, hFilter, newPolId, hCritD)
        elif type == 'infra_metric':
            kName = cond['name']
            kFilter = ""
            if 'filter' in cond:
                kFilter = cond['filter']
            kEvent = cond['event_type']
            kValue = cond['select_value']
            kCompare = cond['comparison']
            kCrit = cond['critical_threshold']['value']
            kCritD = cond['critical_threshold']['duration_minutes']
            kTime = cond['critical_threshold']['time_function']
            createInfraMetric(type, kName, kFilter, kEvent, newPolId, kValue, kCompare, kCrit, kCritD, kTime)
        else:
            print('Infrastructure condition type unknown!')
            print('Type returned as: ' + str(type))

def postNRQLConditionsToNewAccount(polId, conds):
    endpoint = 'https://api.newrelic.com/v2/alerts_nrql_conditions/policies/' + str(polId) + '.json'
    for cond in conds['nrql_conditions']:
        payload = {
            "nrql_condition": {
            "name": cond['name'],
            "enabled": cond['enabled'],
            "terms": [
            {
                "duration": cond['terms'][0]['duration'],
                "operator": cond['terms'][0]['operator'],
                "priority": cond['terms'][0]['priority'],
                "threshold": cond['terms'][0]['threshold'],
                "time_function": cond['terms'][0]['time_function']
            }
            ],
            "value_function": cond['value_function'],
            "nrql": {
                "query": cond['nrql']['query'],
                "since_value": cond['nrql']['since_value']
            }
            }
        }
        print("Creating NRQL condition: " + str(cond['name']))
        r = requests.post(endpoint, headers=postHeaderz, json=payload)
        if str(r.status_code)[:1] == '2':
            resp = r.json()
            print("Success! Created NRQL Condition: " + str(cond['name']))
        else:
            print("Error Occurred! Status Code: " + str(r.status_code))
            print(r.content)

def postAPMConditionsToNewAccount(polId, conds):
    api = 'https://api.newrelic.com/v2/alerts_conditions/policies/' + str(polId) + '.json' #policy ID used here to assign conditions
    for cond in conds['conditions']:
        if 'violation_close_timer' in cond and cond['type'] == 'apm_app_metric':
            payload = {
                "condition": {
                    "type": cond['type'],
                    "name": cond['name'],
                    "enabled": cond['enabled'],
                    "entities": [],
                "condition_scope": cond['condition_scope'],
                "metric": cond['metric'],
                "violation_close_timer": cond['violation_close_timer'],
                "terms": cond['terms']
                }
            }
        elif 'violation_close_timer' in cond and cond['type'] == 'apm_jvm_metric':
            payload = {
                "condition": {
                    "type": cond['type'],
                    "name": cond['name'],
                    "enabled": cond['enabled'],
                    "entities": [],
                    "metric": cond['metric'],
                    "violation_close_timer": cond['violation_close_timer'],
                    "terms": cond['terms']
                }
            }
        elif cond['type'] == 'apm_kt_metric':
            payload = {
                "condition": {
                    "type": cond['type'],
                    "name": cond['name'],
                    "enabled": cond['enabled'],
                    "entities": [],
                    "metric": cond['metric'],
                    "terms": cond['terms']
                }
            }
        elif cond['type'] == 'browser_metric':
            payload = {
                "condition": {
                    "type": cond['type'],
                    "name": cond['name'],
                    "enabled": cond['enabled'],
                    "entities": [],
                    "metric": cond['metric'],
                    "terms": cond['terms']
                }
            }
        else:
            payload = {
                "condition": {
                    "type": cond['type'],
                    "name": cond['name'],
                    "enabled": cond['enabled'],
                    "entities": [
                    ],
                "condition_scope": cond['condition_scope'],
                "metric": cond['metric'],
                "terms": cond['terms']
                }
            }

        # post condition
        print ("Creating APM Condition: " + str(cond['name']))
        apm_req = requests.post(api, json=payload, headers=postHeaderz)
        if str(apm_req.status_code)[:1] == '2':
            print(cond['name'] + ' was successfully created!')
            resp = apm_req.json()
        else:
            print('Failure! Response code: ' + str(apm_req.status_code))
            print(apm_req.content)

def postSynConditionToNewAccount(pID, cond):
    print(cond)
    api = 'https://api.newrelic.com/v2/alerts_synthetics_conditions/policies/' + str(pID) + '.json'
    print("Creating Synthetic Condition: " + str(cond['name']))
    payload = {
        "synthetics_condition": {
            "name": cond['name'],
            "monitor_id": cond['monitor_id'],
            "enabled": cond['enabled']
        }
    }
    syn_req = requests.post(api, json=payload, headers=postHeaderz)
    if (str(syn_req.status_code)[:1] == '2'):
        print(cond['name'] + ' was successfully created!')
        resp = syn_req.json()
    else:
        print('Failure! Response code: ' + str(syn_req.status_code))
        resp = syn_req.json()
        print(resp)


def postPluginConditionsToNewAccount(polId, conds):
    api = 'https://api.newrelic.com/v2/alerts_plugins_conditions/policies/' + str(polId) + '.json'
    for cond in conds['plugins_conditions']:
        payload = {
            "plugins_condition": {
                "name": cond['name'],
                "enabled": "true",
                "entities": [],
                "metric_description": cond['metric_description'],
                "metric": cond['metric'],
                "value_function": cond['value_function'],
                "terms": cond['terms'],
                "plugin": cond['plugin']
            }
        }

        print("Creating Plugin Condition: " + str(cond['name']))
        plugin_req = requests.post(api, json=payload, headers=postHeaderz)
        if str(plugin_req.status_code)[:1] == '2':
            print(cond['name'] + ' was successfully created!')
            resp = plugin_req.json()
        else:
            print('Failure! Response code: ' + str(plugin_req.status_code))
            resp = plugin_req.json()
            if (resp['error']['title'] == 'Invalid plugin.'):
                print("Plugin: '" + cond['plugin']['guid'] + "' not reporting to target account. Please validate that plugin is reporting data.")
            else:
                print(resp)

def createNewPolicy(polName, incident_pref):
    headerz = {'X-Api-Key': str(new_admin_key), 'Content-Type': 'application/json'}
    payload = {
        "policy": {
            "incident_preference": str(incident_pref),
            "name": str(polName)
        }
    }
    print("Creating policy: " + str(polName) + " in target account.")
    pol_url = 'https://api.newrelic.com/v2/alerts_policies.json'
    r = requests.post(pol_url, data=json.dumps(payload), headers=headerz)
    if r.status_code == 201:
        print('Created policy: ' + polName + " successfully!")
        resp = r.json()
        id = resp['policy']['id']
    else:
        print("Status Code: " + str(r.status_code))
        print(r.content)
    return id

def createInfraMetric(kType, kName, kFilter, kEvent, polID, kValue, kCompare, kCrit, kCritD, kTime):
    if kFilter == "":
        payload = {
            "data":{
                "type":kType,
                "name":kName,
                "enabled": bool("true"),
                "policy_id": polID,
                "event_type":kEvent,
                "select_value":kValue,
                "comparison":kCompare,
                "critical_threshold":{
                    "value": kCrit,
                    "duration_minutes": kCritD,
                    "time_function": kTime
                }
            }
        }
    else:
        payload = {
            "data":{
                "type":kType,
                "name":kName,
                "enabled": bool("true"),
                "filter": kFilter,
                "policy_id": polID,
                "event_type":kEvent,
                "select_value":kValue,
                "comparison":kCompare,
                "critical_threshold":{
                    "value": kCrit,
                    "duration_minutes": kCritD,
                    "time_function": kTime
                }
            }
        }

    print("Creating Infrastructure Condition: " + str(kName))
    infra_req = requests.post(infra_post_api, json=payload, headers=postHeaderz)
    if infra_req.status_code == 201:
        print(str(kName) + ' was successfully created!')
    else:
        print('Fail! Response code: ' + str(infra_req.status_code))
        print(infra_req.content)

def createHostNotReporting(hType, hName, hFilter, polId, hCritD):
    if hFilter == "":
        payload = {
            "data":{
                "type": hType,
                "name": hName,
                "enabled": bool("true"),
                "policy_id": polId,
                "critical_threshold":{
                    "duration_minutes": hCritD
                }
            }
        }
    else:
        payload = {
            "data":{
                "type": hType,
                "name": hName,
                "enabled": bool("true"),
                "filter": hFilter,
                "policy_id": polId,
                "critical_threshold":{
                    "duration_minutes": hCritD
                }
            }
        }

    print("Creating Infrastructure Condition: " + str(hName))
    infra_req = requests.post(infra_post_api, json=payload, headers=postHeaderz)
    if infra_req.status_code == 201:
        print(str(hName) + ' was successfully created!')
    else:
        print('Fail! Response code: ' + str(infra_req.status_code))
        print(infra_req.content)

def createProcessNotRunning(iType, iName, iFilter, polID, iCompare, iCrit, iCritD, iProc):
    if iFilter == "" or iProc == "":
        payload = {
            "data":{
                "type":iType,
                "name":iName,
                "enabled": bool("true"),
                "filter": iFilter,
                "policy_id": polID,
                "comparison":iCompare,
                "critical_threshold":{
                    "value": iCrit,
                    "duration_minutes": iCritD,
                }
            }
        }
    else:
        payload = {
            "data":{
                "type":iType,
                "name":iName,
                "enabled": bool("true"),
                "policy_id": polID,
                "comparison":iCompare,
                "critical_threshold":{
                    "value": iCrit,
                    "duration_minutes": iCritD,
                },
                "process_filter": iProc
            }
        }
    print("Creating Infrastructure Condition: " + str(iName))
    infra_req = requests.post(infra_post_api, json=payload, headers=postHeaderz)
    if infra_req.status_code == 201:
        print(str(iName) + ' was successfully created!')
    else:
        print('Fail! Response code: ' + str(infra_req.status_code))
        print(infra_req.content)

def main():
    #open and parse config file
    with open("migration-config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    global admin_key
    global new_admin_key
    global new_graph_key
    global new_account_id
    global policyNames
    global postHeaderz

    admin_key = cfg['admin_key']
    new_admin_key = cfg['new_admin_key']
    new_graph_key = cfg['new_graph_key']
    new_account_id = cfg['new_account_id']
    policyNames = cfg['policyNames']
    postHeaderz = {'X-Api-Key': str(new_admin_key), 'Content-Type': 'application/json'}

    for existingPolicy in policyNames: #for each existing policy specified
        existingPolId, inc_p = getPolicy(existingPolicy) # get ID of an existing policy (in old account)
        polId = createNewPolicy(existingPolicy, inc_p) # create existing policy in new account (returns a new policy ID)

        s = getSyntheticConditions(existingPolId)
        if (len(s['synthetics_conditions']) > 0):
            for synCond in s['synthetics_conditions']:
                monName = getExistingMonitorName(synCond['monitor_id'])
                newId = getNewMonitorId(monName)
                if (newId != 'none'):
                    del synCond['id']
                    synCond['monitor_id'] = newId
                    postSynConditionToNewAccount(polId, synCond)

        c = getInfraConditions(existingPolId) # get the infra conditions for that policy based upon ID from the old account
        if len(c['data']) > 0:
            postInfraConditionsToNewAccount(polId, c) #using new policy ID, post existing conditions to new account

        z = getNRQLConditions(existingPolId)
        if len(z['nrql_conditions']) > 0:
            postNRQLConditionsToNewAccount(polId, z)

        a = getAPMConditions(existingPolId)
        if len(a['conditions']) > 0:
            postAPMConditionsToNewAccount(polId, a)

        p = getPluginConditions(existingPolId)
        if len(p['plugins_conditions']) > 0:
            postPluginConditionsToNewAccount(polId, p)

main()
