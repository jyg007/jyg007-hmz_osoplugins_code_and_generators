# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import base64
import hashlib
import json
import logging
import os
import sys
import time
import urllib
import uuid

import consts
import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from requests.exceptions import RequestException

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


def get_token():

    challenge = str(uuid.uuid4())

    # private_key_data = os.environ["SK"].replace("\\n", "\n").encode('utf-8')
    private_key_data = base64.b64decode(os.environ["SK"])
    private_key = load_pem_private_key(private_key_data, password=None)

    signature = private_key.sign(bytes(challenge, "utf-8"), ec.ECDSA(hashes.SHA256()))

    url = "https://auth." + os.environ["HMZ_SERVER"] + "/token"

    # Define the data payload as a dictionary
    data = {
        "client_id": "customer_api",
        "grant_type": "password",
        "challenge": challenge,
        "public_key": os.environ["PUB"],
        "signature": base64.b64encode(signature).decode("utf-8"),
    }

    rootcertb64 = os.environ.get("ROOTCERT", False)
    if rootcertb64:
        rootcert = base64.b64decode(os.environ["ROOTCERT"]).decode("utf-8")
        with open("/tmp/cert.pem", "w") as file:
            file.write(rootcert)
        tlsrootcert = "/tmp/cert.pem"
    else:
        tlsrootcert = False

    # Send the POST request
    response = requests.post(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        verify=tlsrootcert,
    )

    if response.status_code == 200:
        tmp_r = json.loads(response.text)
        return tmp_r["access_token"], tlsrootcert
    else:
        return "ERROR", False


def bulk_download(to_dir=consts.PREPARED_DIR):
    token, tlsrootcert = get_token()
    if token == "ERROR":
        return "ERROR"
    os.makedirs(to_dir, exist_ok=True)
    # h = { 'Authorization' : 'Bearer '+ os.environ["BEARER_TOKEN"] }
    # response = requests.get("https://"+os.environ["HMZ_API_SERVER"]+"/v1/vaults/"+os.environ["VAULTID"],headers=h)
    # print(response.json())

    rootcertb64 = os.environ.get("ROOTCERT", False)
    if rootcertb64:
        rootcert = base64.b64decode(os.environ["ROOTCERT"]).decode("utf-8")
        with open("/tmp/cert.pem", "w") as file:
            file.write(rootcert)
        tlsrootcert = "/tmp/cert.pem"
    else:
        tlsrootcert = False

    file_path = to_dir + "/" + os.environ["VAULTID"]
    try:
        response = requests.get(
            "https://api."
            + os.environ["HMZ_SERVER"]
            + "/v1/vaults/"
            + os.environ["VAULTID"]
            + "/operations/prepared",
            headers={"Authorization": "Bearer " + token},
            stream=True,
            verify=tlsrootcert,
        )
        response.raise_for_status()
    except RequestException as e:
        print(f"An error occurred: {e}")
        return "ERROR", 500
    else:
        with open(file_path, "wb") as out_file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                out_file.write(chunk)
        logger.info("Download finished successfully")

        with open(file_path, "r") as f_j:
            jcontents = json.load(f_j)
            # logger.info(json.dumps(jcontents))
            for i in jcontents["transactions"]:
                content = {
                    "vaultId": jcontents["vaultId"],
                    "accounts": [],
                    "transactions": [i],
                    "manifests": [],
                }
                filepath = os.path.join(consts.PREPARED_DIR, i["transactionId"])
                with open(filepath, "w") as outfile:
                    json.dump(content, outfile)
            for i in jcontents["accounts"]:
                content = {
                    "vaultId": jcontents["vaultId"],
                    "accounts": [i],
                    "transactions": [],
                    "manifests": [],
                }
                filepath = os.path.join(consts.PREPARED_DIR, i["accountId"])
                with open(filepath, "w") as outfile:
                    json.dump(content, outfile)
            for i in jcontents["manifests"]:
                content = {
                    "vaultId": jcontents["vaultId"],
                    "accounts": [],
                    "transactions": [],
                    "manifests": [i],
                }
                filepath = os.path.join(consts.PREPARED_DIR, i["manifestId"])
                with open(filepath, "w") as outfile:
                    json.dump(content, outfile)
        os.remove(file_path)
        return consts.PREPARED_DIR


def bulk_upload(from_dir=consts.SIGNED_DIR):
    token, tlsrootcert = get_token()
    if token == "ERROR":
        return "ERROR", 500

    for filename in os.listdir(from_dir):
        filepath = os.path.join(from_dir, filename)

    v_tx = []
    v_ac = []
    v_ma = []
    v_va = []

    for filename in os.listdir(from_dir):
        filepath = os.path.join(from_dir, filename)
        f_j = open(filepath, "r")
        jcontents = json.load(f_j)
        for i in jcontents["transactions"]:
            v_tx.append(i)
        for i in jcontents["accounts"]:
            v_ac.append(i)
        for i in jcontents["manifests"]:
            v_ma.append(i)
        for i in jcontents["vaults"]:
            v_ma.append(i)
        os.remove(filepath)
        f_j.close

    content = {
        "accounts": v_ac,
        "transactions": v_tx,
        "manifests": v_ma,
        "vaults": v_va,
    }

    filepath = os.path.join(from_dir, "bulk")

    with open(filepath, "w") as outfile:
        json.dump(content, outfile)

    files = {"files": ("bulk", open(filepath, "rb"))}

    data = {"files": open(filepath, "rb")}

    try:
        response = requests.post(
            "https://api." + os.environ["HMZ_SERVER"] + "/v1/vaults/operations/signed",
            headers={"Authorization": "Bearer " + token},
            files=data,
            verify=tlsrootcert,
        )
        response.raise_for_status()
    except RequestException as e:
        print(f"An error occurred: {e}")
        return "ERROR", 500

    os.remove(filepath)


def backend_status():
    return "OK", 200
