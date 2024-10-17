# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import copy
import json
import logging
import os
import pathlib
import sys
import uuid
from typing import Dict, List, Optional, Tuple

import consts
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(InsecureRequestWarning)

session = requests.Session()
session.headers.update({"X-SSL-CERT": "Path to cert"})
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


def get_backend_endpoint():
    backend_endpoint = os.environ.get("BACKEND_ENDPOINT")
    if not backend_endpoint:
        raise Exception("BACKEND_ENDPOINT not found")
    return backend_endpoint


def save_documents(
    documents: List[Dict], to_dir=consts.PREPARED_DIR
) -> Optional[Exception]:
    try:
        output_dir = pathlib.Path(to_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for document in documents:
            document_id = document.get("id")
            if document_id is None:
                logger.warning("Could not get document id")
                continue

            document_path = None
            try:
                document_path = output_dir.joinpath(document_id)
            except Exception as e:
                logger.warning(
                    f"Could not create path with {output_dir} / {document_id},"
                    f" Error: {e}"
                )
                continue

            document_content = document.get("content")
            if document_content is None:
                logger.warning(f"Document {document_id} does not have any content")
                continue

            with document_path.open("w") as document_file:
                document_file.write(document_content)

    except Exception as e:
        return e


def bulk_upload(from_dir: str = consts.PREPARED_DIR) -> Optional[Exception]:
    try:
        dir_path = pathlib.Path(from_dir)

        vault_id = None
        transactions = []
        accounts = []
        manifests = []

        for filepath in dir_path.iterdir():
            try:
                if filepath.is_file():
                    with filepath.open("r") as document:
                        contents = json.load(document)

                        transactions.extend(contents.get("transactions", []))
                        accounts.extend(contents.get("accounts", []))
                        manifests.extend(contents.get("manifests", []))

                        if vault_id is None:
                            vault_id = contents.get("vaultId")

                    filepath.unlink()
            except Exception as e:
                logger.warning(f"Issue with {filepath}, Error: {e}")

        if not vault_id:
            return Exception("Could not get vault id")

        content = {
            "vaultId": vault_id,
            "accounts": accounts,
            "transactions": transactions,
            "manifests": manifests,
        }

        vault_file = dir_path.joinpath(vault_id)
        with vault_file.open("w") as outfile:
            json.dump(content, outfile)

        files = {"files": (vault_id, vault_file.open("rb"))}

        requests.post(f"{get_backend_endpoint()}/v1/feed/upload", files=files)

        vault_file.unlink()

    except Exception as e:
        return e


def bulk_download(
    to_dir: str = consts.SIGNED_DIR,
) -> Tuple[List[Dict], Optional[Exception]]:
    try:
        dir_path = pathlib.Path(to_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        response = requests.get(f"{get_backend_endpoint()}/v1/feed/download?clean=True")
        response.raise_for_status()

        response_json = response.json()

        empty_content = {
            "accounts": [],
            "transactions": [],
            "manifests": [],
            "vaults": [],
        }

        def write_document_set(content_key: str, id_key: str):
            for item in response_json.get(content_key, []):
                try:
                    content = copy.deepcopy(empty_content)

                    content.setdefault(content_key, []).append(item)

                    document_path = dir_path.joinpath(item.get(id_key))
                    with document_path.open("w") as document:
                        json.dump(content, document)
                except Exception as e:
                    logger.warning(f"Could not write {item.get(id_key)}, Error: {e}")

        for content_key, id_key in [
            ("transactions", "transactionId"),
            ("accounts", "accountId"),
            ("manifests", "manifestId"),
        ]:
            write_document_set(content_key, id_key)

        documents = []

        for file in dir_path.iterdir():
            if file.is_file():
                with file.open("r") as f:
                    documents.append(
                        {"id": file.name, "content": f.read(), "metadata": ""}
                    )
                file.unlink()

        return documents, None

    except Exception as e:
        return [], e


def backend_status():
    try:
        url = f"{get_backend_endpoint()}/v1/feed/status"
        response = session.get(url, timeout=3)
        response.raise_for_status()
        return "OK", 200
    except Exception as e:
        logger.error(f"Backend status exception: {e}")
        return "Unavailable", 503
