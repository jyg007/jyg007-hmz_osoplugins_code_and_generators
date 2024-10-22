# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import base64
import copy
import json
import logging
import os
import pathlib
import sys
import tempfile
import uuid
from typing import IO, Optional, Tuple, Union

import requests
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from . import consts

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


def write_root_cert(
    root_cert_file: IO[bytes],
) -> Tuple[Union[str, bool], Optional[Exception]]:
    try:
        root_cert_b64 = os.environ.get("ROOTCERT")

        if root_cert_b64:
            rootcert = base64.b64decode(root_cert_b64)
            root_cert_file.write(rootcert)
            root_cert_file.seek(0)
            return root_cert_file.name, None
        else:
            return True, None

    except Exception as e:
        return True, e


def get_token(verify: Union[str, bool]) -> Tuple[str, Optional[Exception]]:
    challenge = str(uuid.uuid4())

    private_key_b64 = os.environ.get("SK")
    if not private_key_b64:
        return "", Exception("Could not get SK")

    hmz_server = os.environ.get("HMZ_SERVER")
    if not hmz_server:
        return "", Exception("Could not get HMZ_SERVER")

    public_key = os.environ.get("PUB")
    if not public_key:
        return "", Exception("Could not get PUB")

    private_key_decoded = base64.b64decode(private_key_b64)
    private_key = load_pem_private_key(private_key_decoded, password=None)

    signature = private_key.sign(bytes(challenge, "utf-8"), ec.ECDSA(hashes.SHA256()))

    url = f"https://auth.{hmz_server}/token"

    data = {
        "client_id": "customer_api",
        "grant_type": "password",
        "challenge": challenge,
        "public_key": public_key,
        "signature": base64.b64encode(signature).decode("utf-8"),
    }

    response = requests.post(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        verify=verify,
    )

    try:
        response.raise_for_status()
        response_json = response.json()
        token = response_json.get("access_token")
        if not token:
            return "", Exception("Could not get token from response json")
        return token, None
    except Exception as e:
        return "", e


def bulk_download(to_dir=consts.PREPARED_DIR) -> Tuple[str, Optional[Exception]]:
    dir_path = pathlib.Path(to_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    hmz_server = os.environ.get("HMZ_SERVER")
    if not hmz_server:
        return "", Exception("Could not get HMZ_SERVER")

    vault_id = os.environ.get("VAULTID")
    if not vault_id:
        return "", Exception("Could not get env variable VAULTID")

    with tempfile.NamedTemporaryFile() as root_cert_file:
        root_cert_verify, err = write_root_cert(root_cert_file)
        if err:
            logger.warning(f"Could not write root cert, Error: {err}")

        token, err = get_token(root_cert_verify)
        if err:
            return "", err

        vault_path = dir_path.joinpath(vault_id)

        url = f"https://api.{hmz_server}/v1/vaults/{vault_id}/operations/prepared"

        response = None
        try:
            response = requests.get(
                url,
                headers={"Authorization": "Bearer " + token},
                stream=True,
                verify=root_cert_verify,
            )
            response.raise_for_status()
        except Exception as e:
            return "", e

        with vault_path.open("wb") as vault_file:
            for chunk in response.iter_content(chunk_size=1024):
                vault_file.write(chunk)
        logger.info("Download finished successfully")

        empty_content = {
            "vaultId": "",
            "accounts": [],
            "transactions": [],
            "manifests": [],
        }

        vault_json = None
        with vault_path.open("r") as vault_file:
            vault_json = json.load(vault_file)

        def write_document_set(content_key: str, id_key: str) -> Optional[Exception]:
            for item in vault_json.get(content_key, []):
                content = copy.deepcopy(empty_content)

                content["vaultId"] = vault_json["vaultId"]
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

        os.remove(vault_path)
        return consts.PREPARED_DIR, None


def bulk_upload(from_dir=consts.SIGNED_DIR) -> Optional[Exception]:
    dir_path = pathlib.Path(from_dir)
    dir_path.mkdir(parents=True, exist_ok=True)

    hmz_server = os.environ.get("HMZ_SERVER")
    if not hmz_server:
        return Exception("Could not get HMZ_SERVER")

    vault_id = os.environ.get("VAULTID")
    if not vault_id:
        return Exception("Could not get env variable VAULTID")

    with tempfile.NamedTemporaryFile() as root_cert_file:
        root_cert_verify, err = write_root_cert(root_cert_file)
        if err:
            logger.warning(f"Could not write root cert, Error: {err}")

        token, err = get_token(root_cert_verify)
        if err:
            return err

        for filename in os.listdir(from_dir):
            bulk_file_path = os.path.join(from_dir, filename)

        vaults = []
        transactions = []
        accounts = []
        manifests = []

        for bulk_file_path in dir_path.iterdir():
            try:
                if bulk_file_path.is_file():
                    with bulk_file_path.open("r") as document:
                        contents = json.load(document)

                        transactions.extend(contents.get("transactions", []))
                        accounts.extend(contents.get("accounts", []))
                        manifests.extend(contents.get("manifests", []))
                        vaults.extend(contents.get("vaults", []))

                    bulk_file_path.unlink()
            except Exception as e:
                return e

        content = {
            "accounts": accounts,
            "transactions": transactions,
            "manifests": manifests,
            "vaults": vaults,
        }

        bulk_file_path = dir_path.joinpath("bulk")

        with bulk_file_path.open("w") as bulk_file:
            json.dump(content, bulk_file)

        try:
            with bulk_file_path.open("rb") as bulk_file:
                data = {"files": bulk_file}

                url = f"https://api.{hmz_server}/v1/vaults/operations/signed"

                response = requests.post(
                    url,
                    headers={"Authorization": "Bearer " + token},
                    files=data,
                    verify=root_cert_verify,
                )
                response.raise_for_status()
        except Exception as e:
            return e
        finally:
            os.remove(bulk_file_path)


def backend_status():
    return "OK", 200
