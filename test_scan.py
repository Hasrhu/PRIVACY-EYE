import urllib.request, json, io
from PIL import Image

# 1. Login
data = json.dumps({'email': 'founder@privacyeye.ai', 'password': 'SuperPassword123!'}).encode()
req = urllib.request.Request('http://127.0.0.1:8000/api/v1/auth/login', data=data, headers={'Content-Type': 'application/json'})
res = urllib.request.urlopen(req)
token = json.loads(res.read().decode())['access_token']

# 2. Generate a test image
img = Image.new('RGB', (200, 200), color=(220, 38, 38))
img_bytes = io.BytesIO()
img.save(img_bytes, format='JPEG')
img_bytes.seek(0)
file_data = img_bytes.read()

# 3. Multipart form upload
boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
body = (
    f'--{boundary}\r\n'
    f'Content-Disposition: form-data; name="file"; filename="test_scan.jpg"\r\n'
    f'Content-Type: image/jpeg\r\n\r\n'
).encode() + file_data + f'\r\n--{boundary}--\r\n'.encode()

req = urllib.request.Request('http://127.0.0.1:8000/api/v1/analyze/image', data=body)
req.add_header('Authorization', f'Bearer {token}')
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

res = urllib.request.urlopen(req)
result = json.loads(res.read().decode())
print('Scan complete! Analysis ID:', result['id'])
print('Risk Level:', result['risk_level'])
print('Synthetic Prob:', result['synthetic_probability'])
print('Signals found:', len(result['signals']))
for s in result['signals']:
    print(f" - {s['signal_label']}: {s['severity']}")
