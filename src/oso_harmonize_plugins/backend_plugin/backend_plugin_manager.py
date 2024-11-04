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
        self.seed = os.environ.get("SEED", "")

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

        empty_content = {
            "accounts": [],
            "transactions": [],
            "manifests": [],
            "vaults": [],
        }

        def write_document_set(documents, content_key: str, id_key: str):
            for item in response_json.get(content_key, []):
                self.logger.info(
                    f"Saving document from {content_key} for bulk download"
                )

                try:
                    document_id = item.get(id_key)
                    self.logger.info(f"Saving document {document_id} for bulk download")

                    content = copy.deepcopy(empty_content)
                    content.setdefault(content_key, []).append(item)

                    # Encrypt content
                    if len(self.seed) > 0:
                        data = crypt.encrypt(json.dumps(content), self.seed)
                    else:
                        data = json.dumps(content)

                    documents.append(
                        {"id": item.get(id_key), "content": data, "metadata": ""}
                    )

                    self.logger.info(
                        f"Successfully saved document {document_id} for bulk download"
                    )
                except Exception as err:
                    self.logger.exception(err)
                    continue

        documents = []
        for content_key, id_key in [
            ("transactions", "transactionId"),
            ("accounts", "accountId"),
            ("manifests", "manifestId"),
        ]:
            write_document_set(documents, content_key, id_key)

        return documents

    def bulk_upload(self, documents):
        vault_id = None
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

                if vault_id is None:
                    vault_id = contents.get("vaultId")

                self.logger.info(
                    f"Successfully saved document {document_id} for bulk upload"
                )
            except Exception as e:
                self.logger.exception(e)
                continue

        if not vault_id:
            return Exception("Could not get vault id")

        content = {
            "vaultId": vault_id,
            "accounts": accounts,
            "transactions": transactions,
            "manifests": manifests,
        }

        self.logger.info("Performing bulk upload to backend")

        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as vault_file:
                json.dump(content, vault_file)

            files = {"files": (vault_id, open(vault_file.name, "rb"))}
            response = requests.post(
                url=f"{self.backend_endpoint}/v1/feed/upload",
                files=files,
            )
            response.raise_for_status()
        except Exception as e:
            raise e
        finally:
            os.remove(vault_file.name)

        self.logger.info("Bulk upload finished successfully")
