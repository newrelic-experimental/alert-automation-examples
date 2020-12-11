# Alert-Creation

New Relic Alerting Creation
===========================
Parses config file to create a single alert policy, many alert conditions, and assigns notification channels. Currently only handles APM/Infrastructure/NRQL conditions and email notification channels.


### Requirements

* Python 3+
* New Relic Account & valid admin API key

### Configuration - newAlert.py
### Global
* **HTTP/HTTPS PROXY** -  Your proxy to be used in requests (if ran on box behind firewall)
* **Admin Key** - Valid Admin key generated from New Relic account you are assigning policy to.
* **Policy Name** - Name of your alert policy that will contain multiple conditions/metrics
* **Incident Preference** - Frequency of creation of incidents- Options are **PER_CONDITION** and **PER_POLICY**
  * **PER_CONDITION** - Will trigger a single incident per each condition within policy.
  * **PER_POLICY** - Will trigger only a single incident at a time for any number of conditions violated for a given policy.
* **Emails to add** - Emails to add to policy created; if emails listed do no exist, the script will create them and assign them to the policy.
* **pagerduty_title** - Unique name for your Pagerduty Channel. For more information on integrating PagerDuty visit: https://www.pagerduty.com/docs/guides/new-relic-integration-guide/
* **pagerduty_key** - Your PagerDuty service key.


### APM
If no apm_condition_names are specified, this section will be ignored.

* **app_names** - List format of application names to be added to APM conditions. **NAMES SPECIFIED MUST MATCH APP NAME WITHIN APM CONFIG FILE OR UI**
* **metric_types** - List of types of metrics required by API call- currently available for apm are "**apm_app_metric**" and "**apm_kt_metric**" For more information on available types: https://docs.newrelic.com/docs/alerts/rest-api-alerts/new-relic-alerts-rest-api/alerts-conditions-api-field-names#metric
* **apm_condition_names** - List of desired condition titles to name condition created
* **apm_condition_metrics** - List of desired metrics to alert on - list available at https://docs.newrelic.com/docs/alerts/rest-api-alerts/new-relic-alerts-rest-api/alerts-conditions-api-field-names#metric
* **apm_condition_duration** - List of durations before warning or critical threshold creates an event. For example, "create critical incident after 15 minutes"
* **apm_condition_critT** - List of critical thresholds before an event/alert is fired off.
* **apm_condition_warnT** - List of warning thresholds before an event is fired off.
* **apm_cond_operators** - List of conditional operators to specify when to create an event. Available options are: "above", "below", "equal".
* **apm_custom_metrics** - List of full path to custom metrics desired for condition- will only read this list if **user_defined** is specified in apm_condition_metrics list. To find the full path to a custom metric, use the Data Explorer within Insights.
* **apm_value_functions** - List of operators that determines custom metric's returned value threshold. For example, if my custom metric is "currentThreadCount", I can specify if I want to create an event/alert based upon the min, max, or average of that returned value. Available options: Average, min, max, total, sample_size.

### Infrastructure
If no infra_condition_names are specified, this section is ignored.

* **metric_types** - List of types of metrics required by API call- for a complete list visit: https://docs.newrelic.com/docs/infrastructure/new-relic-infrastructure/infrastructure-alert-conditions/rest-api-calls-new-relic-infrastructure-alerts#definitions
* **infra_condition_names** - List of desired names for each condition created
* **eventType** - List of buckets where each "selectValue" metric sits (ex- ProcessSample, StorageSample, SystemSample)- More information on available types can be found at https://docs.newrelic.com/docs/infrastructure/new-relic-infrastructure/data-instrumentation/default-infrastructure-attributes-events
* **filterClause** - List of filter criteria to assign matching hosts to.
* **selectValue** - Desired metric names to trigger an event from.
* **infra_comparison** - List of conditional operators to specify when to create an event. Available options are: "above", "below", "equal".
* **criticalT** - List of critical thresholds before an event/alert is fired off.
* **warningT** -  List of warning thresholds before an event is fired off.
* **crit_durations** - List of durations before critical threshold creates an event.
* **warn_durations** - List of durations before warning threshold creates an event.


### NRQL
If no nrql_condition_names are specified, this section is ignored.

* **nrql_condition_names** - Names of your conditions.
* **nrql_durations** - Duration before the trigger creates an event or alert.
* **nrql_operators** - List of conditional operators to specify when to create an event. Available options are: "above", "below", "equal".
* **nrql_priority** - Event classification as "critical" or "warning"
* **nrql_thresholds** - Value to to check query result against- (Ex- If query result = nrql_threshold value, fire an event).
* **nrql_time_functions** - Available options: "any" or "all"-- **"any"** specifies an event to be created if the threshold specified is violated "at least once in" a specific time period. "all" specifies an event to be created if a threshold specified is violated "for at least" a specific time period. Example: **"all"** = Query returns a value above 5 **for at least** x time period. **"any"** = Query returns a value above 5 **at least once in** x time period.
* **nrql_value_functions** - Available options: "single_value" or "sum" -- **"single_value"** specifies if the query returns a value above/below/equal to your threshold specified. **"sum"** specifies if the sum of the query result is above/below/equal to your threshold.
* **nrql_queries** -  NRQL queries to execute.
* **nrql_since_values** - Time in which query is evaluated. Available options are 1,2,3,4,or 5 minutes. Example: with the since_value set to 3 minutes and the query set to ‘SELECT count(*) FROM myEvent’, the resulting value of the query ‘SELECT count(*) FROM myEvent SINCE 3 minutes ago UNTIL 2 minutes ago’ will be evaluated against the nrql_threshold value once per minute. Due to the way NRQL data is aggregated, a ‘since value’ of 3 or higher is recommended to prevent false positives.

### `config.yml` format
```
---
#GLOBAL
GLOBAL:
  http_proxy: 'INSERT HERE'
  https_proxy: 'INSERT HERE'
  admin_key: 'Your-Admin-key'
  inc_pref: 'PER_CONDITION'
  policy_name: 'TestPolicy1'

#emails to assign to policy, if email in list doesn't exist-- it will get created as a new notification channel and assigned to policy created above.
emails_to_add: ['kpeet@newrelic.com', 'khpeet@svsu.edu', 'test2@google.com']

#PagerDuty channel to create and assign to policy; Leave blank if not being used.
pagerduty_title: MyPagerDutyChannel
pagerduty_key: '20405067339956032'


#APM - Each condition name, must have a corresponding, metric, duration, critical threshold, warning threshold, and operator.
#***NOTE: Each application (app_name) specified will get assigned to ALL conditions listed.
#For more information on available metric types, visit https://docs.newrelic.com/docs/alerts/rest-api-alerts/new-relic-alerts-rest-api/alerts-conditions-api-field-names#metric
#IF apm_condition_names is NULL [], this section will be ignored
APM:
  app_names: ['Snakes-Java', 'Tomcat-Local']  #***Match your New Relic APM config file app_name (case-sensitive)
  metric_types: ['apm_app_metric', 'apm_app_metric', 'apm_app_metric']
  apm_condition_names: ['Apdex - Low', 'Error Rate - High', 'Current Thread Count - Low']
  apm_condition_metrics: ['apdex', 'error_percentage', 'user_defined']
  apm_condition_duration: [15, 10, 15]
  apm_condition_critT: [.7, 5, 1]
  apm_condition_warnT: [.85, 3, 2]
  apm_cond_operators: ['below', 'above', 'below']

  #Use apm_custom fields only if 'user_defined' is specified for an apm_condition_metric above
  apm_custom_metrics: ['JMX/Catalina/ThreadPool/"ajp-nio-8009"/currentThreadCount'] #actual metric to measure (full path)
  apm_value_functions: ['average'] #average, min, max, total, sample_size.


#INFRA - Each condition name must have a corresponding eventType, filterClause, threshold, etc (all fields required)
#For more information on available types or for more assistance, visit https://docs.newrelic.com/docs/infrastructure/new-relic-infrastructure/infrastructure-alert-conditions/rest-api-calls-new-relic-infrastructure-alerts
#IF infra_condition_names is NULL [], this section will be ignored
INFRA:
  metric_types: [infra_metric, infra_metric, infra_metric] #infra_host_not_reporting, infra_metric, infra_process_running
  infra_condition_names: ['CPU % (High)', 'Disk Utilization (High)', 'Memory % (High)']
  eventType: [SystemSample, SystemSample, SystemSample]
  filterClause: ["`technology` LIKE '%tomcat%'", "`technology` LIKE '%tomcat%'", "`technology` LIKE '%tomcat%'"]
  selectValue: [cpuPercent, diskUsedPercent, memoryUsedPercent]
  infra_comparison: [above, above, above]
  criticalT: [90, 90, 90]
  warningT: [85, 85, 85]
  crit_durations: [10, 10, 10]
  warn_durations: [15, 15, 15]

#NRQL - Each condition name must have a corresponding duration, operator, etc.
#For more information on NRQL Alerting visit -- https://docs.newrelic.com/docs/alerts/new-relic-alerts/defining-conditions/create-alert-conditions-nrql-queries
#If nrql_condition_names is Null [], this section will be ignored.
NRQL:
  nrql_condition_names: ['NRQL-Test'] #Title for conditions
  nrql_durations: [15] # Duration of the condition to fire event after threshold breached
  nrql_operators: [above] # above, below, equal
  nrql_priority: [critical] # critical or warning
  nrql_thresholds: [5] # value to check query against
  nrql_time_functions: [all] #any or all
  nrql_value_functions: [single_value] #single_value or sum;
  nrql_queries: [
  "SELECT average(cpuPercent) FROM SystemSample where hostname = 'ip-172-31-17-47'"
  ] #NRQL queries to be checked.
  nrql_since_values: [3] #time which query is checked (1-5 minutes), Default is 3;

```

### NOTES
* Each application specified will get assigned to **ALL** conditions listed.
* For each metric type/name, all other values are 1-1. For example in the example config above the first filterClause specified will only be associated with the CPU High condition and first list item for critical, warning thresholds/durations.
* When migrating APM conditions, entities will not automatically be assigned by default.
* Infrastructure conditions will not be available to edit in the UI once pushed via API (limitation)
