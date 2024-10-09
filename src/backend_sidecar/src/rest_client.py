# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import os
import pathlib
import uuid

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

session = requests.Session()
session.headers.update({"X-SSL-CERT": "Path to cert"})


def get_backend_endpoint():
    backend_endpoint = os.environ.get("BACKEND_ENDPOINT")
    if not backend_endpoint:
        raise Exception("BACKEND_ENDPOINT not found")
    return backend_endpoint


def upload_prepared_doc(filepath) -> requests.Response | Exception:
    try:
        url = f"{get_backend_endpoint()}/feed/upload"
        filepath = pathlib.Path(filepath)
        with filepath.open("rb") as file:
            files = {"files": (filepath.name, file)}
            response = session.post(url=url, files=files)
            response.raise_for_status()
        return response
    except Exception as e:
        return e


def download_signed_file(save_dir):
    try:
        url = f"{get_backend_endpoint()}/feed/download?clean=true"
        response = session.get(url=url)
        return write_document(response, save_dir)
    except Exception as e:
        return e


def write_document(
    response: requests.Response, save_dir: str
) -> pathlib.Path | None | Exception:
    if "Content-Disposition" not in response.headers:
        return None

    dir_path = pathlib.Path(save_dir)
    dir_path.mkdir(parents=True, exist_ok=True)
    filename = str(uuid.uuid4())
    filepath = dir_path.joinpath(filename)

    try:
        with filepath.open("wb") as f:
            f.write(response.content)
        return filepath
    except Exception as e:
        return e


def status():
    url = f"{get_backend_endpoint()}/feed/status"
    try:
        response = session.get(url, timeout=3)
        response.raise_for_status()
        return "OK", 200
    except Exception as e:
        return "Unavailable", 503
