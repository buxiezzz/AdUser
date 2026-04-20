import urllib.request
import urllib.parse
import json
import base64
import os

login_url = "http://localhost:18000/api/auth/login"
login_data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'}).encode('utf-8')
req = urllib.request.Request(login_url, data=login_data, method="POST")
req.add_header('Content-Type', 'application/x-www-form-urlencoded')
try:
    with urllib.request.urlopen(req) as response:
        token = json.loads(response.read().decode('utf-8')).get('access_token')
except Exception as e:
    print("Login err:", e)
    exit()

# Try to upload file using multipart/form-data
BOUNDARY = '----------BOUNDARY_7965412'
CRLF = b'\r\n'
filepath = "test_assets.xlsx"
filename = os.path.basename(filepath)
with open(filepath, 'rb') as f:
    file_bytes = f.read()

body = []
body.append(f'--{BOUNDARY}'.encode('utf-8'))
body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode('utf-8'))
body.append(b'Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
body.append(b'')
body.append(file_bytes)
body.append(f'--{BOUNDARY}--'.encode('utf-8'))
body.append(b'')
req_body = b'\r\n'.join(body)

import_url = "http://localhost:18000/api/assets/import"
req2 = urllib.request.Request(import_url, data=req_body, method="POST")
req2.add_header('Authorization', f'Bearer {token}')
req2.add_header('Content-Type', f'multipart/form-data; boundary={BOUNDARY}')

try:
    with urllib.request.urlopen(req2) as resp:
        print("Import response:", resp.getcode(), resp.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"Import failed! HTTP {e.code}: {e.read().decode('utf-8')}")
except Exception as e:
    print("Err importing:", e)
