
import time
import json
import urllib.request
import urllib.parse
import concurrent.futures
import sys

BASE_URL = "http://localhost:8000/api/v1"

def make_request(method, url, data=None, files=None):
    # Basic multipart/form-data implementation for file upload
    if files:
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
        body = []
        
        # Add fields
        if data:
            for key, value in data.items():
                body.append(f'--{boundary}')
                body.append(f'Content-Disposition: form-data; name="{key}"')
                body.append('')
                body.append(str(value))
        
        # Add files
        for key, (filename, filedata, content_type) in files.items():
            body.append(f'--{boundary}')
            body.append(f'Content-Disposition: form-data; name="{key}"; filename="{filename}"')
            body.append(f'Content-Type: {content_type}')
            body.append('')
            # filedata is bytes
            pass # We handle bytes concatenation later
            
        body.append(f'--{boundary}--')
        body.append('')
        
        # Construct full body
        full_body = b''
        
        # Add fields
        if data:
            for key, value in data.items():
                full_body += f'--{boundary}\r\n'.encode()
                full_body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
                full_body += f'{value}\r\n'.encode()
                
        for key, (filename, filedata, content_type) in files.items():
             full_body += f'--{boundary}\r\n'.encode()
             full_body += f'Content-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'.encode()
             full_body += f'Content-Type: {content_type}\r\n\r\n'.encode()
             full_body += filedata
             full_body += b'\r\n'
             
        full_body += f'--{boundary}--\r\n'.encode()
        
        req = urllib.request.Request(url, data=full_body, method=method)
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    else:
        if data:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data, method=method)
            req.add_header('Content-Type', 'application/json')
        else:
            req = urllib.request.Request(url, method=method)
            
    try:
        with urllib.request.urlopen(req) as response:
            return {
                'status_code': response.status,
                'json': json.loads(response.read().decode())
            }
    except urllib.error.HTTPError as e:
        return {
            'status_code': e.code,
            'json': json.loads(e.read().decode()) if e.code != 404 else {'detail': 'Not Found'}
        }
    except Exception as e:
        return {'status_code': 0, 'error': str(e)}

def create_image(color):
    # Simple BMP image generation
    # BMP header (14 bytes) + DIB header (40 bytes) + Pixel Data
    # 1x1 pixel 24-bit
    bmp = (
        b'BM\x3a\x00\x00\x00\x00\x00\x00\x00\x36\x00\x00\x00' + # Header
        b'\x28\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x01\x00\x18\x00' + # DIB
        b'\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
        b'\x00\x00\x00\x00\x00\x00\x00\x00'
    )
    if color == 'red':
        pixel = b'\x00\x00\xFF' # BGR
    else:
        pixel = b'\xFF\x00\x00' # BGR
    
    return bmp + pixel + b'\x00' # Padding to 4 bytes

def register_case(name="Test Case"):
    img_data = create_image('red')
    
    files = {'photo': ('test.bmp', img_data, 'image/bmp')}
    data = {
        'name': name,
        'age': '25',
        'last_seen': 'Mumbai',
        'submitted_by': 'TestAdmin'
    }
    
    start = time.time()
    response = make_request('POST', f"{BASE_URL}/cases", data=data, files=files)
    end = time.time()
    print(f"Register Case Status: {response.get('status_code')}, Time: {end - start:.2f}s")
    return response.get('json', {}).get('id')

def submit_sighting(location="Mumbai"):
    img_data = create_image('blue')
    
    files = {'photo': ('sighting.bmp', img_data, 'image/bmp')}
    data = {
        'location': location,
        'mobile': '1234567890'
    }
    
    start = time.time()
    response = make_request('POST', f"{BASE_URL}/public", data=data, files=files)
    end = time.time()
    print(f"Submit Sighting Status: {response.get('status_code')}, Time: {end - start:.2f}s")
    return response.get('json', {}).get('id')

def run_matching():
    start = time.time()
    # Query params need to be handled manually in URL for urllib
    response = make_request('POST', f"{BASE_URL}/matching/run?tolerance=0.6")
    end = time.time()
    print(f"Matching Status: {response.get('status_code')}, Time: {end - start:.2f}s")
    print("Match Result:", response.get('json'))

if __name__ == "__main__":
    print("--- Starting Verification ---")
    
    # 1. Test Performance (Concurrent Requests)
    print("\n--- Testing Concurrent Submissions (Async Check) ---")
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(register_case, f"Concurrent {i}") 
            for i in range(3)
        ]
        concurrent.futures.wait(futures)
        
    sighting_id = submit_sighting()
    case_id = register_case("Match Target")
    
    run_matching()
    
    # Clean up
    print("\n--- Cleaning Up ---")
    if case_id:
        make_request('DELETE', f"{BASE_URL}/cases/{case_id}")
    if sighting_id:
        make_request('DELETE', f"{BASE_URL}/public/{sighting_id}")
