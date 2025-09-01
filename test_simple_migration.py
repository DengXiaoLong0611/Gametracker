#!/usr/bin/env python3
import requests
import json

BASE_URL = "https://gametracker-m37i.onrender.com"

print("Calling force migration API...")
response = requests.post(f"{BASE_URL}/api/admin/force-migrate")
print(f"Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print(f"Success: {result.get('success')}")
    print(f"Message: {result.get('message')}")
    if 'log' in result:
        print("Logs:")
        for entry in result['log']:
            print(f"  {entry}")
else:
    print(f"Error: {response.text}")