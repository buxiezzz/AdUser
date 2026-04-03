import urllib.request
import urllib.error
import urllib.parse
import json

# 1. Login
login_url = "http://localhost:18000/api/auth/login"
login_data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'}).encode('utf-8')
req = urllib.request.Request(login_url, data=login_data, method="POST")
req.add_header('Content-Type', 'application/x-www-form-urlencoded')

try:
    with urllib.request.urlopen(req) as response:
        res = json.loads(response.read().decode('utf-8'))
        token = res.get('access_token')
except Exception as e:
    print("Login err:", e)
    exit()

# 2. Get assets to test delete
assets_url = "http://localhost:18000/api/assets/"
req2 = urllib.request.Request(assets_url, method="GET")
req2.add_header('Authorization', f'Bearer {token}')
try:
    with urllib.request.urlopen(req2) as response:
        assets = json.loads(response.read().decode('utf-8'))
        print(f"Got {len(assets)} assets")
        if assets:
            asset_to_delete = assets[0]['id']
            # 3. Batch Delete
            del_url = "http://localhost:18000/api/assets/batch-delete"
            del_data = json.dumps({"asset_ids": [asset_to_delete]}).encode('utf-8')
            req3 = urllib.request.Request(del_url, data=del_data, method="POST")
            req3.add_header('Authorization', f'Bearer {token}')
            req3.add_header('Content-Type', 'application/json')
            with urllib.request.urlopen(req3) as del_res:
                print("Delete res:", del_res.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"Auth or request failed! {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print("Err2:", e)
