#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

import copy
import json
import logging
import os
import sys
import tempfile
from typing import Dict, List

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

from oso_harmonize_plugins.common import crypt, errors

urllib3.disable_warnings(InsecureRequestWarning)


class BackendPluginManager:
    def __init__(self):
        if "BACKEND_ENDPOINT" not in os.environ:
            raise errors.ConfigError("BACKEND_ENDPOINT not found")
        self.backend_endpoint = os.environ["BACKEND_ENDPOINT"]
        self.seed = os.environ.get("OSOENCRYPTIONPASS", "")

        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def backend_status(self):
        response = requests.get(
            f"{self.backend_endpoint}/v1/feed/status",
            timeout=3,
        )
        response.raise_for_status()

    def bulk_download(self) -> List[Dict]:
        response = requests.get(f"{self.backend_endpoint}/v1/feed/download?clean=True")
        response.raise_for_status()
        response_json = response.json()
        self.logger.info("Bulk download finished successfully")

        documents = []

        sections = [
            ("transactions", "transactionId", "transaction"),
            ("accounts", "accountId", "account"),
            ("manifests", "manifestId", "manifest"),
        ]

        for section, id_key, type_name in sections:
            for item in response_json.get(section, []):
                # Encrypt if seed is set
                if self.seed and "signedPayload" in item:
                    item["signedPayloadCiphered"] = crypt.encrypt(item["signedPayload"], self.seed)
                    del item["signedPayload"]

                # Build content and metadata
                content = {
                    "accounts": [item] if section == "accounts" else [],
                    "transactions": [item] if section == "transactions" else [],
                    "manifests": [item] if section == "manifests" else [],
                    "vaults": [],
                }
                meta = {"source": item["vaultId"], "type": type_name}

                documents.append({
                    "id": item[id_key],
                    "content": json.dumps(content),
                    "metadata": json.dumps(meta)
                })

        return documents

    def bulk_upload(self, documents):
        v_tx= {}
        v_ac= {}
        v_ma= {}

        self.logger.info("Saving documents for bulk upload")
        for document in documents:
            try:
                contents = json.loads(document["content"])
                vaultid= contents.get("vaultId")

                if vaultid not in v_tx:
                    v_tx[vaultid]=[]
                    v_ac[vaultid]=[]
                    v_ma[vaultid]=[]
                # Map sections to their storage dict
                section_map = {
                    "transactions": v_tx[vaultid],
                    "accounts": v_ac[vaultid],
                    "manifests": v_ma[vaultid],
                }

                for section, storage in section_map.items():
                    for item in contents.get(section, []):
                        if self.seed and "signedPayloadCiphered" in item:
                            item["signedPayload"] = crypt.decrypt(item["signedPayloadCiphered"], self.seed)
                            del item["signedPayloadCiphered"]
                        storage.append(item)

                self.logger.info(f"Saving document {document['id']} for bulk upload")
               
            except Exception as e:
                self.logger.exception(e)
                continue

        self.logger.info("Performing bulk upload to backend")
        for vaultid in v_tx.keys():  
            content = {
                "vaultId": vaultid,
                "accounts": v_ac[vaultid],
                "transactions": v_tx[vaultid],
                "manifests": v_ma[vaultid],
            }

            try:
                with tempfile.NamedTemporaryFile(mode="w", delete=False) as vault_file:
                    json.dump(content, vault_file)

                files = {"files": (vaultid, open(vault_file.name, "rb"))}
                response = requests.post(
                    url=f"{self.backend_endpoint}/v1/feed/upload",
                    files=files,
                )
                response.raise_for_status()
                self.logger.info(f"Successfully uploaded vault {vaultid}")
            except requests.HTTPError as http_err:
                self.logger.error(f"HTTP error uploading vault {vaultid}: {http_err} - {response.text}")
            except Exception as err:
                self.logger.error(f"Unexpected error uploading vault {vaultid}: {err}")
 
        self.logger.info("Bulk upload finished successfully")
