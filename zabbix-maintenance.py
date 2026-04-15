#!/usr/bin/python
import requests
import json
import sys
from datetime import datetime, timedelta



# Zabbix API configuration
ZABBIX_API_URL = "http://localhost/zabbix/api_jsonrpc.php"
ZABBIX_API_TOKEN = "6b4439a83c39fb0833d64180295620e7b8afd63238c44ec80dcbde7846ed9c68"  # Replace with your provided auth token

def get_host_id(auth_token, hostname):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "filter": {
                "host": [hostname]
            }
        },
        "id": 2
    }
    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {auth_token}"
    }
    response = requests.post(ZABBIX_API_URL, json=payload, headers=headers)
    try:
        response_json = response.json()
        # print("DEBUG host.get response:", response_json)  # tijdelijke debug
        result = response_json.get('result', [])
        if result:
            return result[0]['hostid']
        else:
            raise Exception(f"Host '{hostname}' not found.")
    except Exception as e:
        raise Exception(f"Failed to retrieve host ID: {e}")

def create_maintenance(auth_token, host_id, user_description, duration, collect_data=True):
    start_time = int(datetime.now().timestamp())
    end_time = int((datetime.now() + timedelta(hours=duration)).timestamp())
    end_string = (datetime.now() + timedelta(hours=duration)).strftime("%d/%m/%y at %H:%M:%S %Z")

    payload = {
        "jsonrpc": "2.0",
        "method": "maintenance.create",
        "params": {
            "name": f"UserMaintenance for host {hostname}",
            "description": f"Created by {user_description} from host menu on "+datetime.now().strftime("%d/%m/%y at %H:%M:%S %Z")+f". Duration: {duration} hours. "+f"Ends on: {end_string}",
            "active_since": start_time,
            "active_till": end_time,
            "maintenance_type": 0 if collect_data else 1,
            "timeperiods": [{
                "timeperiod_type": 0,
                "start_date": start_time,
                "period": duration * 3600
            }],
            "hosts": [{
                "hostid": host_id
            }]
        },
        "id": 3
    }

    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {auth_token}"
    }

    response = requests.post(ZABBIX_API_URL, json=payload, headers=headers)
    try:
        response_json = response.json()
        if 'result' in response_json:
            return response_json['result']
        elif 'error' in response_json:
            raise Exception(f"Zabbix API error: {response_json['error']['data']}")
        else:
            raise Exception(f"Unexpected response: {response_json}")
    except json.JSONDecodeError:
        raise Exception(f"Invalid JSON response: {response.text}")

def delete_maintenance(auth_token, hostname):
    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {auth_token}"
    }

    host_id = get_host_id(auth_token, hostname)

    payload = {
        "jsonrpc": "2.0",
        "method": "maintenance.get",
        "params": {
            "output": "extend",
            "selectHosts": ["hostid"],
            "search": { "name": "UserMaintenance"
                } 
        },
        "id": 4
    }

    response = requests.post(ZABBIX_API_URL, json=payload, headers=headers)
    maintenances = response.json().get('result', [])

    # print("DEBUG maintenance.get response:", maintenances)  # tijdelijke debug

    maintenance_ids = [
        m['maintenanceid']
        for m in maintenances
        if any(h['hostid'] == host_id for h in m.get('hosts', []))
    ]

    if not maintenance_ids:
        print(f"No active maintenance found for host '{hostname}'")
        return

    delete_payload = {
        "jsonrpc": "2.0",
        "method": "maintenance.delete",
        "params": maintenance_ids,
        "id": 5
    }

    del_response = requests.post(ZABBIX_API_URL, json=delete_payload, headers=headers)
    del_result = del_response.json()
    if 'result' in del_result:
        print(f"Deleted {len(del_result['result']['maintenanceids'])} maintenance(s) for host '{hostname}'")
    elif 'error' in del_result:
        print(f"Error deleting maintenance: {del_result['error']['data']}")

def main(action, hostname, user_description, duration=None, collect_data=True):
    auth_token = ZABBIX_API_TOKEN
    try:
        if action.lower() == "create":
            if duration is None:
                raise ValueError("Missing duration for maintenance.")
            host_id = get_host_id(auth_token, hostname)
            delete_maintenance(auth_token, hostname)
            result = create_maintenance(auth_token, host_id, user_description, duration, collect_data)
            print(f"✅ Maintenance #{result['maintenanceids'][0]} created, "+f"data collection: {'Enabled' if collect_data else 'Disabled'}")
            print(f"Duration: {duration} hours")
            print("Ends on: "+(datetime.now() + timedelta(hours=duration)).strftime("%d/%m/%y at %H:%M:%S %Z"))
        elif action.lower() == "delete":
            delete_maintenance(auth_token, hostname)
        else:
            print("Invalid action. Use 'create' or 'delete'.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage:")
        print("  Create: script.py create <hostname> <user_description> <duration> [yes|no]")
        print("  Delete: script.py delete <hostname>")
    else:
        action = sys.argv[1]
        hostname = sys.argv[2]
        user_description = sys.argv[3] if len(sys.argv) > 3 and action.lower() == "create" else None
        duration = int(sys.argv[4]) if len(sys.argv) > 4 and action.lower() == "create" else None
        collect_data = True if len(sys.argv) < 6 or sys.argv[5].lower() == "yes" else False
        main(action, hostname, user_description, duration, collect_data)
