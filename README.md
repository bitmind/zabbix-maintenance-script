# Zabbix maintenance script

Python script for manual host action which creates and delete a maintenance period on a single host

Based on https://github.com/Trikke76/Zabbix/tree/master/maintenance

## Features

* Uses Zabbix API from python
* Delete maintenance: will delete only maintenances with name "UserMaintenance". Other maintenance rules applied to the host will not be affected.
* When creating maintenance, it will try to delete existing maintenances: this will allow users to "extend" maintenance period without requiring to delete the existing one.
* Maintenance description will contain: maintenance start time, duration, end time and user which created it.
 
 
## Requirements
* Zabbix 7.0
* python
 
## How to use 
 * Create a dedicated Zabbix user for the script (with LIMITED role permissions). Don't use Admin or normal users: API token will be written in cleartext in the script.
 * Create an API token for that user 
 * Copy script on a secure directory on the Zabbix Server host, chmod 700
 * Configure the script with API URL and API token.
 * Create a Script for maintenance creation
 * Create a Script for maintenance deletion
 
 (see attache screenshots)
 
 