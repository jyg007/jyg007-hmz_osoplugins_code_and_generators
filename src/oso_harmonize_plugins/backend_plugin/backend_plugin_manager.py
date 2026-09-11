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
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

from oso_harmonize_plugins.common import crypt, errors

urllib3.disable_warnings(InsecureRequestWarning)

# (counter prefix in the cold-bridge status payload, category key in uploads)
SIGNING_CATEGORIES = (
    ("transaction", "transactions"),
    ("account", "accounts"),
    ("manifest", "manifests"),
    ("rewraps", "rewraps"),
    ("backups", "backups"),
)

class BackendPluginManager:
    def __init__(self):
        if "BACKEND_ENDPOINT" not in os.environ:
            raise errors.ConfigError("BACKEND_ENDPOINT not found")
        self.backend_endpoint = os.environ["BACKEND_ENDPOINT"]
        self.seed = os.environ.get("OSOENCRYPTIONPASS", "")
        self.whitelisting = os.environ.get("WHITELISTING", "0")
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.state_file = os.environ.get( "SIGNING_STATE_FILE", "/tmp/backend_signing_state.json")
        self.signing_stall_secs = int(os.environ.get("SIGNING_STALL_SECS", "300"))

        vaultids = os.environ.get("VAULTIDS") or os.environ.get("VAULTID")

        if not vaultids:
            raise errors.ConfigError("VAULTID or VAULTIDS not found")

        self.VAULTIDS = {v.strip() for v in vaultids.replace(",", " ").split() if v.strip()}

    def _state_file(self, vaultid):
        base, ext = os.path.splitext(self.state_file)
        return f"{base}_{vaultid}{ext}"

    def _load_signing_state(self,vaultid):
        try:
            with open(self._state_file(vaultid)) as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    def _save_signing_state(self, vaultid,state):
        try:
            with open(self._state_file(vaultid), "w") as f:
                json.dump(state, f)
        except OSError as e:
            self.logger.error(f"Could not persist signing state: {e}")

    def _clear_signing_state(self,vaultid):
        try:
            os.remove(self._state_file(vaultid))
        except OSError:
            pass

    def backend_status(self):
        statuses = {}
        for vaultid in self.VAULTIDS:
            try:
               response = requests.get(
                   f"{self.backend_endpoint}-{vaultid}:8080/v1/feed/status",
                   timeout=3,
               )
               response.raise_for_status()

               state = self._load_signing_state(vaultid)
               if state is None:
                   continue
       
               try:
                   counters = response.json()
               except ValueError:
                   self.logger.warning(
                       "vaultid={vaultid} Cold-bridge status response is not JSON;"
                       " skipping signing-progress check"
                   )
                   return
       
               expected = state.get("expected", {})
               pending = {}
               shortfall = {}
               for prefix, category in SIGNING_CATEGORIES:
                   to_sign = int(counters.get(f"{prefix}ToSign") or 0)
                   signed = int(counters.get(f"{prefix}Signed") or 0)
                   if to_sign > 0:
                       pending[category] = to_sign
                   #  remaining = max(to_sign - signed, 0)

                   #  if remaining > 0:
                   #    pending[category] = remaining
                   # Guard the window where the cold vault has not yet registered the
                   # uploaded feed: all-zero counters right after an upload mean
                   # "not started", not "done".
                   if signed < int(expected.get(category, 0)):
                       shortfall[category] = int(expected.get(category, 0)) - signed
               if not pending and not shortfall:
                   self.logger.info(f"Signing complete, vaultid={vaultid}, feed counters: {counters}")
                   self._clear_signing_state(vaultid)
                   return
        
               now = time.time()
               if counters != state.get("last_counters"):
                   state["last_counters"] = counters
                   state["last_progress_at"] = now
                   self._save_signing_state(vaultid,state)
               elif now - state.get("last_progress_at", now) > self.signing_stall_secs:
                   self.logger.error(
                       f"Signing stalled for over {self.signing_stall_secs}s with"
                       f" operations outstanding (pending={pending},"
                       f" shortfall={shortfall}, counters={counters});"
                       " reporting ready with a partial result set"
                   )
                   self._clear_signing_state(vaultid)
                   return
        
               self.logger.info(f"Signing in progress, vaultid={vaultid}, feed counters: {counters}")
               raise errors.SigningInProgress(f"vaultid={vaultid} pending={pending}")

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

        sections = [
            ("transactions", "transactionId", "transaction"),
            ("accounts", "accountId", "account"),
            ("manifests", "manifestId", "manifest"),
            ("rewraps", "rewrapSecretMaterialsId", "rewrap"),
            ("backups", "backupId", "backup"),
        ]

        for vaultid in self.VAULTIDS:
                response = requests.get(
                    f"{self.backend_endpoint}-{vaultid}:8080/v1/feed/download?clean=true"
                )
                response.raise_for_status()

                response_json = response.json()

                self.logger.info(
                    "Bulk download batch received for vaultid %s",
                    vaultid
                )

                for section, id_key, type_name in sections:
                    for item in response_json.get(section, []):
                        # Encrypt if seed is set
                        if self.seed and "signedPayload" in item:
                            item["signedPayloadCiphered"] = crypt.encrypt(
                                item["signedPayload"],
                                self.seed
                            )
                            del item["signedPayload"]

                        content = {
                            "accounts": [item] if section == "accounts" else [],
                            "transactions": [item] if section == "transactions" else [],
                            "manifests": [item] if section == "manifests" else [],
                            "rewraps": [item] if section == "rewraps" else [],
                            "backups": [item] if section == "backups" else [],
                            "vaults": [],
                        }

                        meta = {
                            "source": item["vaultId"],
                            "type": type_name
                        }

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
                    "rewraps": [],
                    "transactions": [ input_obj ],
                    "manifests": [],
                    "backups": [],
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
        v_re= {}
        v_ba= {}

        self.logger.info("Saving documents for bulk upload")
        for document in documents:
            try:
                contents = json.loads(document["content"])
                vaultid= contents.get("vaultId")

                if vaultid not in v_tx:
                    v_tx[vaultid]=[]
                    v_ac[vaultid]=[]
                    v_ma[vaultid]=[]
                    v_re[vaultid]=[]
                    v_ba[vaultid]=[]
                # Map sections to their storage dict
                section_map = {
                    "transactions": v_tx[vaultid],
                    "accounts": v_ac[vaultid],
                    "manifests": v_ma[vaultid],
                    "rewraps": v_re[vaultid],
                    "backups": v_ba[vaultid],
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
                      "rewraps": v_re[vaultid],
                      "backups": v_ba[vaultid],
                    }
                else: 
                    self.logger.info(f"No whitelist file found for vaultid {vaultid}")
                    content = {
                      "vaultId": vaultid,
                      "accounts": v_ac[vaultid],
                      "transactions": [] ,
                      "manifests": v_ma[vaultid],
                      "rewraps": v_re[vaultid],
                      "backups": v_ba[vaultid],
                    }
            else:
                content = {
                  "vaultId": vaultid,
                  "accounts": v_ac[vaultid],
                  "transactions": v_tx[vaultid],
                  "manifests": v_ma[vaultid],
                  "rewraps": v_re[vaultid],
                  "backups": v_ba[vaultid],
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

                now = time.time()
                self._save_signing_state( vaultid,
                    {
                        "expected": {
                            "transactions": len(v_tx[vaultid]),
                            "accounts": len(v_ac[vaultid]),
                            "manifests": len(v_ma[vaultid]),
                            "backups": len(v_ba[vaultid]),
                        },
                        "uploaded_at": now,
                        "last_progress_at": now,
                        "last_counters": None,
                    }
                )
            except requests.HTTPError as http_err:
                self.logger.error(f"HTTP error uploading vault {vaultid}: {http_err} - {response.text}")
            except Exception as err:
                self.logger.error(f"Unexpected error uploading vault {vaultid}: {err}")
 
        self.logger.info("Bulk upload finished successfully")
