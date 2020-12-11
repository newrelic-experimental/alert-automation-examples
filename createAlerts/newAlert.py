#!usr/bin/python

#########################################################################################################
# Author: Keagan Peet
# Purpose: To create standard alerting policies, conditions, notification channels for new deployments.
# Note: Using python 3
#########################################################################################################

import json
import requests
import yaml

#CREATE POLICY
polID = 0
inc_pref = "" #default
headerz = {}
pol_name = ""
app_names = "" #list should match your app_names in your newrelic agent configs
x = 0ß

def CreateNewPolicy(ip, pn):
        global polIDß
        payload1 = {
            "policy": {
                "incident_preference": ip,
                "name": pn
            }
        }
        print ("Creating Policy: " + str(pn))
        pol_url = 'https://api.newrelic.com/v2/alerts_policies.json'
        policyCreate = requests.post(pol_url, data=json.dumps(payload1), headers=headerz)
        if policyCreate.status_code == 201:
            pol_response = policyCreate.content
            json_formatted= json.loads(pol_response)
            polID = json_formatted['policy']['id']
            print ("Policy Number: " + str(polID) + " successfully created. Storing ID")
            return polID
        else:
            print("Status Code: " + str(policyCreate.status_code))
            print("Policy Creation Failed!")
            print(policyCreate.content)

def CreateAPMCondition(metricType, condTitle, condMetric, condDuration, condCriticalT, condWarnT, condOperator):
    api = 'https://api.newrelic.com/v2/alerts_conditions/policies/' + str(polID) + '.json' #policy ID used here to assign conditions
    payload = {
        "condition": {
            "type": metricType,
            "name": condTitle,
            "enabled": "true",
            "condition_scope": "application",
            "entities": [

            ],
        "metric": condMetric,
        "violation_close_timer": "8",
        "terms": [
        {
            "duration": str(condDuration),
            "operator": condOperator,
            "priority": "critical",
            "threshold": str(condCriticalT),
            "time_function": "all"
        },
        {
            "duration": str(condDuration),
            "operator": condOperator,
            "priority": "warning",
            "threshold": str(condWarnT),
            "time_function": "all"
        }]
        }
    }

  # post condition
    print ("Creating APM Condition: " + str(condTitle))
    apm_req = requests.post(api, json=payload, headers=headerz)
    if apm_req.status_code == 201:
        print(condTitle + ' was successfully created!')
        resp = apm_req.json()
        if resp['condition']['type'] in ('apm_app_metric', 'apm_kt_metric'):
            anID = resp['condition']['id']
            return anID
        else:
            print ("Unknown condition type!")
    else:
        print('Fail! Response code: ' + str(apm_req.status_code))
        print(apm_req.content)

def CreateUserDefinedCondition(metricType, condTitle, condMetric, condDuration, condCriticalT, condWarnT, condOperator, userMetric, userValue):
        api = 'https://api.newrelic.com/v2/alerts_conditions/policies/' + str(polID) + '.json' #policy ID used here to assign conditions
        payload = {
            "condition": {
                "type": metricType,
                "name": condTitle,
                "enabled": "true",
                "condition_scope": "application",
                "entities": [

                ],
            "metric": condMetric,
            "violation_close_timer": "8",
            "terms": [
            {
                "duration": str(condDuration),
                "operator": condOperator,
                "priority": "critical",
                "threshold": str(condCriticalT),
                "time_function": "all"
            },
            {
                "duration": str(condDuration),
                "operator": condOperator,
                "priority": "warning",
                "threshold": str(condWarnT),
                "time_function": "all"
            }],
                "user_defined": {
                    "metric": str(userMetric),
                    "value_function": str(userValue)
                }
            }
        }

      # post condition
        print ("Creating User Defined Condition: " + str(condTitle))
        apm_req = requests.post(api, json=payload, headers=headerz)
        if apm_req.status_code == 201:
            print(condTitle + ' was successfully created!')
            resp = apm_req.json()
            if resp['condition']['type'] in ('apm_app_metric', 'apm_kt_metric'):
                anID = resp['condition']['id']
                return anID
            else:
                print ("Unknown condition type!")
        else:
            print('Fail! Response code: ' + str(apm_req.status_code))
            print(apm_req.content)

#Create Infrastructure Conditions from config
def CreateInfraCondition(iType, iName, iFilter, ieType, iValue, iCompare, iCrit, iWarn, iCritD, iWarnD):
    api = 'https://infra-api.newrelic.com/v2/alerts/conditions'
    #can change to variables via config file
    payload = {
        "data":{
            "type":iType,
            "name":iName,
            "enabled": bool("true"),
            "where_clause": iFilter,
            "policy_id": polID,
            "event_type":ieType,
            "select_value":iValue,
            "comparison":iCompare,
            "critical_threshold":{
                "value": iCrit,
                "duration_minutes": iCritD,
                "time_function":"all" #can be all or any-- all= "for at least", any = "at least once in"
            },
            "warning_threshold":{
                "value": iWarn,
                "duration_minutes": iWarnD,
                "time_function":"all"
            }
        }
    }

    print("Creating Infrastructure Condition: " + str(iName))
    infra_req = requests.post(api, json=payload, headers=headerz)
    if infra_req.status_code == 201:
        print(str(iName) + ' was successfully created!')
    else:
        print('Fail! Response code: ' + str(infra_req.status_code))
        print(infra_req.content)

def CreateNRQLConditon(nName, nDuration, nOperator, nPriority, nThreshold, nTimeFunc, nValueFunc, nQuery, nSinceValue):
    endpoint = 'https://api.newrelic.com/v2/alerts_nrql_conditions/policies/' + str(polID) + '.json'
    payload = {
        "nrql_condition": {
        "name": nName,
        "enabled": bool("true"),
        "terms": [
        {
            "duration": nDuration,
            "operator": nOperator,
            "priority": nPriority,
            "threshold": nThreshold,
            "time_function": nTimeFunc
        }
        ],
        "value_function": nValueFunc,
        "nrql": {
            "query": nQuery,
            "since_value": nSinceValue
        }
        }
    }

    print("Creating NRQL condition: " + str(nName) + "...")
    try:
        r = requests.post(endpoint, headers=headerz, json=payload)
        if str(r.status_code)[:1] == '2':
            resp = r.json()
            print("Success! Created NRQL Condition: " + str(nName))
        else:
            print("Error Occurred! Status Code: " + str(r.status_code))
            print(r.content)
    except IndexError:
        return 'ER'


def GetAPMEntityID(anAppName):
    entityapm = 'https://api.newrelic.com/v2/applications.json'
    print("Getting APM Entity ID for: " + str(anAppName))
    payload = {'filter[name]': str(anAppName)}
    r = requests.get(entityapm, headers=headerz, params=payload)
    if r.status_code == 200:
        response = r.json()
        id = response['applications'][0]['id']
        return id
    else:
        print ("Error! Status code: " + r.status_code)
        print(r.content)

def AssignAPMEntityToCondition(aConditionID, aentityID):
    print ("Assigning defined APM entity to condition...")
    api = 'https://api.newrelic.com/v2/alerts_entity_conditions/' + str(aentityID) + '.json'
    payload = {'entity_type': 'Application', 'condition_id': aConditionID}
    r = requests.put(api, headers=headerz, params=payload)
    if str(r.status_code)[:1] == '2':
        print("Success! Application entity: " + str(aentityID) +" assigned!")
    else:
        print("Failed with status code: " + str(r.status_code))
        print(r.content)

def getChannelIDs():
    api = 'https://api.newrelic.com/v2/alerts_channels.json'
    head = {'X-Api-Key': admin_key}
    cycle = 0
    try_again = 1
    first_time = 1
    channel_dict = {} #key value lookup for email-id
    try:
        print('Obtaining Channel IDs...')
        while try_again == 1:
            payload = {'page': cycle}
            r = requests.get(api, headers=head, params=payload)
            print('Requesting Channels Status Code= ' + str(r.status_code) + '\nCycle: ' + str(cycle))
            channels = r.json()
            if str(r.status_code)[:1] == '2':
                for aChannel in channels['channels']:
                        email = aChannel['name']
                        nID = aChannel['id']
                        channel_dict.update({email: nID})
                if 'next' not in r.links:
                    try_again = 0
            elif str(r.status_code)[:1] == '4':
                print("Error! Invalid request-Check API key or inputs")
            else:
                print("Could not complete request.")
        return channel_dict
    except IndexError:
        return 'ER'

#Takes list of emails to assign to policy originally created
def AssignChannels(emailsToAdd):
    api = 'https://api.newrelic.com/v2/alerts_policy_channels.json'
    channelIDs = getChannelIDs()
    emailList = []
    try:
        print("Adding channels to policy for desired emails")
        headerz = {'X-Api-Key': admin_key}
        for email in emailsToAdd:
            if email in channelIDs.keys():
                emailList.append(channelIDs[email]) #add id to var based on email(key)
            else:
                print('Email ' + str(email) + ' not found, attempting to create channel...')
                newEmailID = CreateEmailChannel(email)
                emailList.append(newEmailID) # add newly created ID to list of channels to add to policy
        emailString = ",".join([str(x) for x in emailList]) # create comma sep list
        payload = {"policy_id": str(polID), "channel_ids": str(emailString)}
        r = requests.put(api,headers=headerz,params=payload)
        if str(r.status_code)[:1] == '2':
            resp = r.json()
            print("Added emails successfully!")
        else:
            print("Error Occurred: " + str(r.status_code))
            print(r.content)
    except IndexError:
        return 'ER'

def AssignPDChanneltoPolicy(pdTitle, pdKey):
    try:
        print("Adding PagerDuty Channel to policy...")
        api = 'https://api.newrelic.com/v2/alerts_policy_channels.json'
        headerz = {'X-Api-Key': admin_key}
        pdID = CreatePagerDutyChannel(pdTitle, pdKey)
        payload = {"policy_id": str(polID), "channel_ids": str(pdID)}
        r = requests.put(api, headers=headerz, params=payload)
        if str(r.status_code)[:1] == '2':
            resp = r.json()
            print("Added PagerDuty Channel successfully!")
        else:
            print("Error Occurred: " + str(r.status_code))
            print(r.content)
    except IndexError:
        return 'ER'

def CreatePagerDutyChannel(pdTitle, pdKey):
    endpoint = 'https://api.newrelic.com/v2/alerts_channels.json'
    pdPayload = {
            "channel": {
            "name": str(pdTitle),
            "type": "pagerduty",
            "configuration": {
                "service_key": str(pdKey)
                }
            }
    }
    try:
        r = requests.post(endpoint, headers=headerz, json=pdPayload)
        if str(r.status_code)[:1] == '2':
            resp = r.json()
            newPDID = resp['channels'][0]['id'] #store ID of new channel created
            return newPDID #return ID to assign to current policy
    except IndexError:
        return 'ER'

def CreateEmailChannel(email):
    endpoint = 'https://api.newrelic.com/v2/alerts_channels.json'
    emailPayload = {
            "channel": {
            "name": str(email),
            "type": "email",
            "configuration": {
		          "recipients": str(email),
		          "include_json_attachment": bool("true")
                  }
             }
    }
    try:
        r = requests.post(endpoint, headers=headerz, json=emailPayload)
        if str(r.status_code)[:1] == '2':
            resp = r.json()
            newID = resp['channels'][0]['id'] #store ID of new channel created
            return newID #return ID to assign to current policy
    except IndexError:
        return 'ER'


def main():
    #open and parse config file
    with open("config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    #GLOBAL Assignments
    global admin_key
    global inc_pref
    global app_names
    global pol_name
    global headerz
    admin_key = cfg['GLOBAL']['admin_key']
    inc_pref = cfg['GLOBAL']['inc_pref']
    pol_name = cfg['GLOBAL']['policy_name']
    headerz = {'X-Api-Key': str(admin_key), 'Content-Type': 'application/json'}
    eAdd = cfg['emails_to_add']
    pdTitle = cfg['pagerduty_title']
    pdKey = cfg['pagerduty_key']

    #Check if any global values missing-- if no, create policy
    if not all((admin_key, inc_pref, pol_name)):
        print("Missing a Global config value! Please verify config.yml")
        exit(1)
    else:
        CreateNewPolicy(inc_pref, pol_name)

    #check and parse APM conditions and assign application based on name
    apm_conds = cfg['APM']['apm_condition_names']
    if not apm_conds:
        print("No APM conditions specified, skipping...")
    else:
        k = 0
        app_names = cfg['APM']['app_names'] # ***THIS SHOULD MATCH APP_NAMES CONFIGURED IN APM AGENT YML
        mType = cfg['APM']['metric_types']
        cNames = cfg['APM']['apm_condition_names']
        cMetrics = cfg['APM']['apm_condition_metrics']
        cDurations = cfg['APM']['apm_condition_duration']
        cCrit = cfg['APM']['apm_condition_critT']
        cWarn = cfg['APM']['apm_condition_warnT']
        cOps = cfg['APM']['apm_cond_operators']
        userMetric = cfg['APM']['apm_custom_metrics']
        userValue = cfg['APM']['apm_value_functions']
        while k < len(apm_conds):
            x=0 #counter for looping through applications to assign to policies.
            z=0 #counter for custom metrics- dependent on if 'user_defined' is specified in apm_condition_metrics
            if cMetrics[k] == 'user_defined':
                aConditionID = CreateUserDefinedCondition(mType[k], cNames[k], cMetrics[k], cDurations[k], cCrit[k], cWarn[k], cOps[k], userMetric[z], userValue[z])
                z+=1
            else:
                aConditionID = CreateAPMCondition(mType[k], cNames[k], cMetrics[k], cDurations[k], cCrit[k], cWarn[k], cOps[k])
            while x < len(app_names):
                aentityID = GetAPMEntityID(app_names[x])
                AssignAPMEntityToCondition(aConditionID, aentityID)
                x+=1
            k+=1

    #check and parse Infrastructure conditions
    infra_conds = cfg['INFRA']['infra_condition_names']
    if not infra_conds:
        print("No Infrastructure conditions specified, skipping...")
    else:
        p = 0
        pType = cfg['INFRA']['metric_types']
        pNames = cfg['INFRA']['infra_condition_names']
        peType = cfg['INFRA']['eventType']
        pFilter = cfg['INFRA']['filterClause']
        pValue = cfg['INFRA']['selectValue']
        pCompare = cfg['INFRA']['infra_comparison']
        pCrit = cfg['INFRA']['criticalT']
        pWarn = cfg['INFRA']['warningT']
        pCritD = cfg['INFRA']['crit_durations']
        pWarnD = cfg['INFRA']['warn_durations']
        while p < len(infra_conds):
            CreateInfraCondition(pType[p], pNames[p], pFilter[p], peType[p], pValue[p], pCompare[p], pCrit[p], pWarn[p], pCritD[p], pWarnD[p])
            p +=1


    #check and parse NRQL conditions
    nrql_conds = cfg['NRQL']['nrql_condition_names']
    if not nrql_conds:
        print("No NRQL conditions specified, skipping...")
    else:
        n = 0
        nName = cfg['NRQL']['nrql_condition_names']
        nDuration = cfg['NRQL']['nrql_durations']
        nOperator = cfg['NRQL']['nrql_operators']
        nPriority = cfg['NRQL']['nrql_priority']
        nThreshold = cfg['NRQL']['nrql_thresholds']
        nTimeFunc = cfg['NRQL']['nrql_time_functions']
        nValueFunc = cfg['NRQL']['nrql_value_functions']
        nQuery = cfg['NRQL']['nrql_queries']
        nSinceValue = cfg['NRQL']['nrql_since_values']
        while n < len(nrql_conds):
            CreateNRQLConditon(nName[n], nDuration[n], nOperator[n], nPriority[n], nThreshold[n], nTimeFunc[n], nValueFunc[n], nQuery[n], nSinceValue[n])
            n +=1

    #Assign channels to policies if not blank in config
    if eAdd == []:
        print("No email notification channels to add! Skipping...")
    else:
        AssignChannels(eAdd)

    if pdTitle != "" and pdKey != "":
         AssignPDChanneltoPolicy(pdTitle, pdKey)
    else:
        print("No PagerDuty channels to add! Skipping...")



main()
