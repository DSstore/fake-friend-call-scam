"""Minimal TLS-verified HTTP support; never log headers or credentials."""
import json
import mimetypes
import urllib.error
import urllib.request
import uuid
from pathlib import Path

def request(url, data=None, headers=None, timeout=180):
    req=urllib.request.Request(url,data=data,headers=headers or {})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        # Do not dump remote payloads, which can contain reflected credentials.
        raise RuntimeError(f'Provider HTTP {exc.code}. Check model, account access, quota and input schema.') from None
    except urllib.error.URLError:
        raise RuntimeError('Provider network request failed. Check connectivity and retry existing job before submitting again.') from None

def json_request(url, payload=None, headers=None):
    data=json.dumps(payload).encode() if payload is not None else None
    hdr={'Content-Type':'application/json',**(headers or {})}
    return json.loads(request(url,data,hdr))

def download(url, destination):
    if not url.startswith('https://'):
        raise ValueError('Provider downloads must use HTTPS.')
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_bytes(request(url))

def multipart(fields, files):
    boundary='scamfilm-'+uuid.uuid4().hex
    parts=[]
    for key,value in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    for key,path in files:
        path=Path(path)
        kind=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"; filename="{path.name}"\r\nContent-Type: {kind}\r\n\r\n'.encode()+path.read_bytes()+b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    return b''.join(parts),f'multipart/form-data; boundary={boundary}'
