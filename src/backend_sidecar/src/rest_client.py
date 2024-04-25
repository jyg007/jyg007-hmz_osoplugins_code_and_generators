# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import os
import uuid
import urllib3, requests
from urllib3.exceptions import InsecureRequestWarning
urllib3.disable_warnings(InsecureRequestWarning)

session = requests.Session()
session.headers.update({'X-SSL-CERT': "Path to cert"})

def get_backend_endpoint():
    if 'BACKEND_ENDPOINT' not in os.environ:
        raise Exception('BACKEND_ENDPOINT not found')
    return os.environ['BACKEND_ENDPOINT']

def upload_prepared_doc(filepath):
    url = get_backend_endpoint() + '/feed/upload'
    filename = filepath.split("/")[-1]
    files = {"files": (filename, open(filepath, 'rb').read())}
    response = session.post(url=url, files=files)
    return response

def download_signed_file(save_dir):
    url = get_backend_endpoint() + '/feed/download?clean=true'
    response = session.get(url=url)
    return write_document(response, save_dir)

def write_document(response, save_dir):
    # Check if attachment is in response
    if 'Content-Disposition' not in response.headers:
        return None
    # make filename unique
    filename = str(uuid.uuid4())
    filepath = os.path.join(save_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(response.content)
    return filepath

def status():
    url = get_backend_endpoint() + '/feed/status'
    try:
        response = session.get(url, timeout=3)
        return 'OK', 200
    except requests.exceptions.HTTPError as e:
        return 'Unavailable', 503
