#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2024
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#

import base64
import copy
import json
import logging
import os
import sys
import tempfile
import uuid
from typing import IO, Tuple, Union


import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from oso_harmonize_plugins.common import crypt, errors

class FrontendPluginManager:
    def __init__(self):
        if "SK" not in os.environ:
            raise errors.ConfigError("SK not found")
        private_key_b64 = os.environ["SK"]
        private_key_decoded = base64.b64decode(private_key_b64)
        self.private_key = load_pem_private_key(private_key_decoded, password=None)
        
        if "HMZ_SERVER" not in os.environ:
            raise errors.ConfigError("HMZ_SERVER not found")
        self.hmz_server = os.environ["HMZ_SERVER"]

        if "PUB" not in os.environ:
            raise errors.ConfigError("PUB not found")
        self.public_key = os.environ["PUB"]

        if "VAULTID" not in os.environ:
            raise errors.ConfigError("VAULTID not found")
        self.vault_id = os.environ["VAULTID"]

        self.seed = os.environ.get("SEED", "")

        self.root_cert_b64 = os.environ.get("ROOTCERT")
        with tempfile.NamedTemporaryFile(delete=False) as root_cert_file:
            self.verify = self._write_root_cert(root_cert_file)

        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _get_token(self) -> str:
        challenge = str(uuid.uuid4())
        signature = self.private_key.sign(bytes(challenge, "utf-8"), ec.ECDSA(hashes.SHA256()))
        data = {
            "client_id": "customer_api",
            "grant_type": "password",
            "challenge": challenge,
            "public_key": self.public_key,
            "signature": base64.b64encode(signature).decode("utf-8"),
        }

        response = requests.post(
            f"https://auth.{self.hmz_server}/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            verify=self.verify,
        )

        response.raise_for_status()
        response_json = response.json()
        token = response_json.get("access_token")
        if not token:
            raise Exception("Could not get token from response json")
        return token

    def _write_root_cert(self, root_cert_file: IO[bytes]) -> Union[str, bool]:
        if self.root_cert_b64:
            rootcert = base64.b64decode(self.root_cert_b64)
            root_cert_file.write(rootcert)
            root_cert_file.seek(0)
            return root_cert_file.name
        else:
            return True, None

    def get_token(self) -> str:
        self.logger.info("Obtaining JWT access token...")
        token = self._get_token()
        self.logger.info("Successfully obtained JWT access token")
        return token

    def bulk_download(self) -> list:
        self.logger.info("Performing bulk download from frontend")
        token = self.get_token()
        response = requests.get(
            url = f"https://api.{self.hmz_server}/v1/vaults/{self.vault_id}/operations/prepared",
            headers = {"Authorization": "Bearer " + token},
            stream = True,
            verify = self.verify,
        )
        response.raise_for_status()
        vault_json = response.json()
        self.logger.info("Bulk download finished successfully")

        empty_content = {
            "vaultId": "",
            "accounts": [],
            "transactions": [],
            "manifests": [],
        }

        def write_document_set(documents, content_key: str, id_key: str):
            for item in vault_json.get(content_key, []):
                self.logger.info(f"Saving document from {content_key} for bulk download")

                try:
                    document_id = item.get(id_key)
                    self.logger.info(f"Saving document {document_id} for bulk download")

                    content = copy.deepcopy(empty_content)
                    content["vaultId"] = vault_json["vaultId"]
                    content.setdefault(content_key, []).append(item)

                    # Encrypt content
                    if len(self.seed) > 0:
                        data = crypt.encrypt(json.dumps(content), self.seed)
                    else:
                        data = json.dumps(content)

                    documents.append({"id": document_id, "content": data, "metadata": ""})

                    self.logger.info(f"Successfully saved document {document_id} for bulk download")
                except Exception as e:
                    self.logger.exception(e)
                    continue

        documents = []
        for content_key, id_key in [
            ("transactions", "transactionId"),
            ("accounts", "accountId"),
            ("manifests", "manifestId"),
        ]: write_document_set(documents, content_key, id_key)

        return documents

    def bulk_upload(self, documents):
        vaults = []
        transactions = []
        accounts = []
        manifests = []

        self.logger.info("Saving documents for bulk upload")
        for document in documents:
            try:
                document_id = document["id"]
                self.logger.info(f"Saving document {document_id} for bulk upload")
                # Decrypt content
                if len(self.seed) > 0:
                    contents = json.loads(crypt.decrypt(document["content"], self.seed))
                else:
                    contents = json.loads(document["content"])

                transactions.extend(contents.get("transactions", []))
                accounts.extend(contents.get("accounts", []))
                manifests.extend(contents.get("manifests", []))
                vaults.extend(contents.get("vaults", []))

                self.logger.info(f"Successfully saved document {document_id} for bulk upload")
            except Exception as e:
                self.logger.exception(e)
                continue

        content = {
            "accounts": accounts,
            "transactions": transactions,
            "manifests": manifests,
            "vaults": vaults,
        }

        self.logger.info("Performing bulk upload to frontend")
        token = self.get_token()
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as vault_file:
                json.dump(content, vault_file)

            files = {"files": open(vault_file.name, 'rb')}
            response = requests.post(
                url = f"https://api.{self.hmz_server}/v1/vaults/operations/signed",
                headers = {"Authorization": "Bearer " + token},
                files = files,
                verify = self.verify,
            )
            response.raise_for_status()
        except Exception as e:
            raise e
        finally:
            os.remove(vault_file.name)
        self.logger.info("Bulk upload finished successfully")

    def backend_status():
        pass
