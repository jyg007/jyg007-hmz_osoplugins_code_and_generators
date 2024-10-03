# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import copy
import json
import os
import pathlib
from typing import Dict, List

import consts
import requests
import rest_client


def save_documents(
    documents: List[Dict], to_dir=consts.PREPARED_DIR
) -> None | Exception:
    try:
        output_dir = pathlib.Path(to_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        for document in documents:
            document_id = document.get("id")
            if document_id is None:
                print("Could not get document id")
                continue

            document_path = None
            try:
                document_path = output_dir.joinpath(document_id)
            except Exception as e:
                print(
                    f"Could not create path with {output_dir} / {document_id},"
                    f" Error: {e}"
                )
                continue

            document_content = document.get("content")
            if document_content is None:
                print(f"Document {document_id} does not have any content")
                continue

            with document_path.open("w") as document_file:
                document_file.write(document_content)

    except Exception as e:
        return e


def bulk_upload(from_dir: str = consts.PREPARED_DIR) -> None | Exception:
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
                print(f"Issue with {filepath}, Error: {e}")

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

        requests.post(
            rest_client.get_backend_endpoint() + "/v1/feed/upload", files=files
        )

        # TODO: Do we need to remove the vault file after it's uploaded?
        # vault_file.unlink()

    except Exception as e:
        return e


def bulk_download(to_dir: str = consts.SIGNED_DIR) -> List[Dict] | Exception:
    try:
        dir_path = pathlib.Path(to_dir)

        response = requests.get(
            rest_client.get_backend_endpoint() + "/v1/feed/download?clean=True"
        )
        response.raise_for_status()

        response_json = response.json()

        empty_content = {
            "accounts": [],
            "transactions": [],
            "manifests": [],
            "vaults": [],
        }

        def write_document_set(content_key: str, id_key: str) -> None | Exception:
            for item in response_json.get(content_key, []):
                content = copy.deepcopy(empty_content)

                content.setdefault(content_key, []).append(item)

                document_path = dir_path.joinpath(item.get(id_key))
                with document_path.open("w") as document:
                    json.dump(content, document)

        for content_key, id_key in [
            ("transactions", "transactionId"),
            ("accounts", "accountId"),
            ("manifests", "manifestId"),
        ]:
            write_document_set(content_key, id_key)

        # TODO: Not sure if the above is too condensed to be readable for customer code
        #
        # def write_document(content, id_key, content_type):
        #     filepath = dir_path / content[id_key]
        #     with filepath.open("w") as outfile:
        #         json.dump(content_type, outfile)
        #
        # for transaction in response_json.get("transactions", []):
        #     write_document(
        #         transaction,
        #         "transactionId",
        #         {
        #             "accounts": [],
        #             "transactions": [transaction],
        #             "manifests": [],
        #             "vaults": [],
        #         },
        #     )
        #
        # for account in response_json.get("accounts", []):
        #     write_document(
        #         account,
        #         "accountId",
        #         {
        #             "accounts": [account],
        #             "transactions": [],
        #             "manifests": [],
        #             "vaults": [],
        #         },
        #     )
        #
        # for manifest in response_json.get("manifests", []):
        #     write_document(
        #         manifest,
        #         "manifestId",
        #         {
        #             "accounts": [],
        #             "transactions": [],
        #             "manifests": [manifest],
        #             "vaults": [],
        #         },
        #     )

        documents = []

        for file in dir_path.iterdir():
            if file.is_file():
                with file.open("r") as f:
                    documents.append(
                        {"id": file.name, "content": f.read(), "metadata": ""}
                    )
                file.unlink()

        return documents

    except Exception as e:
        return e


def backend_status():
    return rest_client.status()
