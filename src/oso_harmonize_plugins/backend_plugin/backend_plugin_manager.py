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
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

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
        self.whitelisting = os.environ.get("WHITELISTING", "0")
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        vaultids = os.environ.get("VAULTIDS") or os.environ.get("VAULTID")

        if not vaultids:
            raise errors.ConfigError("VAULTID or VAULTIDS not found")

        self.VAULTIDS = {v.strip() for v in vaultids.replace(",", " ").split() if v.strip()}

    def backend_status(self):
        statuses = {}

        for vaultid in self.VAULTIDS:
            try:
                response = requests.get(
                    f"{self.backend_endpoint}-{vaultid}:8080/v1/feed/status",
                    timeout=3,
                )
                response.raise_for_status()

                statuses[vaultid] = {
                    "status": "UP",
                    "response": response.json(),
                }

            except requests.RequestException as e:
                self.logger.error("Vault %s is unavailable: %s", vaultid, e)

                statuses[vaultid] = {
                    "status": "DOWN",
                    "error": str(e),
                 }

        return statuses

    def bulk_download(self) -> List[Dict]:
        documents = []
        for vaultid in self.VAULTIDS:
          response = requests.get(f"{self.backend_endpoint}-{vaultid}:8080/v1/feed/download?clean=true")
          response.raise_for_status()
          response_json = response.json()
          self.logger.info("Bulk download finished successfully for vaultid %s",vaultid)


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

    def load_whitelist(self,vaultid):
        whitelist = set()
        whitelist_file = f"/whitelists/whitelist.{vaultid}"
    
        if os.path.isfile(whitelist_file):
            with open(whitelist_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        whitelist.add(line.lower())
    
        self.logger.info(
            "Loaded whitelist for vaultid=%s size=%d",
            vaultid,
            len(whitelist),
        )

        return whitelist

    def decode_payload(self,input_obj,vaultid,whitelist):
        txid = input_obj["transactionId"]
    
        payload = {
                    "vaultId": vaultid,
                    "accounts": [],
                    "transactions": [ input_obj ],
                    "manifests": [],
        }      

        try:
            r = requests.post(
                f"{self.backend_endpoint}-{vaultid}:8080/v1/feed/decode",
                files={
                    "files": (
                        "input.json",
                        io.BytesIO(json.dumps(payload).encode("utf-8"))
                    )
                },
                timeout=10
            )
    
            if r.status_code != 200:
                self.logger.error(f"[{txid}] API returned HTTP {r.status_code}")
                return None
    
            data = r.json()
    
            dest_addr = data[0][0]["data"]["Tx"]["expenses"][0]["dest"]["data"]["Addr"].lower()
    
            if whitelist and dest_addr not in whitelist:
                self.logger.warning(f"Filtered out txid={txid}, dest={dest_addr}")
                return None
            return input_obj
    
        except Exception as e:
            self.logger.exception(f"[{txid}] Failed: {e}")
            return None

    def whitelist_tx(self,input_objects, vaultid,whitelist, max_workers=2):
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.decode_payload, obj,vaultid,whitelist): obj
                for obj in input_objects
            }
    
            for fut in as_completed(futures):
                obj = futures[fut]
                txid = obj["transactionId"]
    
                try:
                    res = fut.result()
                    if res is not None:
                        results.append(res)
                except Exception as e:
                    self.logger.exception(f"[{txid}] worker crash: {e}")

        return results

    def bulk_upload(self, documents): 
        global vaultid
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
            if self.whitelisting == "1":
                list = self.load_whitelist(vaultid)
                if len(list) != 0:
                    filtered= self.whitelist_tx(v_tx[vaultid], vaultid,list) 
                    content = {
                      "vaultId": vaultid,
                      "accounts": v_ac[vaultid],
                      "transactions": filtered,
                      "manifests": v_ma[vaultid],
                    }
                else: 
                    self.logger.info(f"No whitelist file found for vaultid {vaultid}")
                    content = {
                      "vaultId": vaultid,
                      "accounts": v_ac[vaultid],
                      "transactions": [] ,
                      "manifests": v_ma[vaultid],
                    }
            else:
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
                    url=f"{self.backend_endpoint}-{vaultid}:8080/v1/feed/upload",
                    files=files,
                )
                response.raise_for_status()
                self.logger.info(f"Successfully uploaded vault {vaultid}")
            except requests.HTTPError as http_err:
                self.logger.error(f"HTTP error uploading vault {vaultid}: {http_err} - {response.text}")
            except Exception as err:
                self.logger.error(f"Unexpected error uploading vault {vaultid}: {err}")
 
        self.logger.info("Bulk upload finished successfully")
