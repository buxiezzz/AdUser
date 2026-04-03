import urllib.request
import urllib.error
import json

url = "http://localhost:18000/api/assets/batch-delete"
data = json.dumps({"asset_ids": ["0024b80919d34d3bba9f7741d7616296"]}).encode('utf-8')
req = urllib.request.Request(url, data=data, method="POST")
req.add_header('Content-Type', 'application/json')

try:
    with urllib.request.urlopen(req) as response:
        print(f"Status: {response.getcode()}")
        print(f"Response: {response.read().decode('utf-8')}")
except urllib.error.HTTPError as e:
    print(f"Status: {e.code}")
    print(f"Response: {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
