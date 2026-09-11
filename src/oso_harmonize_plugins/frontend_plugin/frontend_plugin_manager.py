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
import time
import uuid
import io
from functools import lru_cache
from typing import IO, Tuple, Union

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from oso_harmonize_plugins.common import crypt, errors, utils


class FrontendPluginManager:
    def __init__(self):
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # HMZ_USER_SK
        private_key_b64 = os.environ.get("HMZ_USER_SK")
        
        if not private_key_b64:
            raise errors.ConfigError("Harmonize OSO user server key not found")
        
        try:
            private_key_decoded = base64.b64decode(
                private_key_b64,
                validate=True,
            )
        except Exception as exc:
            self.logger.error(
                "Failed to decode HMZ_USER_SK: %s",
                exc,
            )
            raise errors.ConfigError(
                "Harmonize OSO user server key is not valid Base64"
            ) from exc
        try:
            self.private_key = load_pem_private_key(
                private_key_decoded,
                password=None,
            )
        except (ValueError, TypeError) as exc:
            self.logger.error(
                "HMZ_USER_SK does not contain a valid PEM private key: %s",
                exc,
            )
            raise errors.ConfigError(
                "Harmonize OSO user server key is not a valid PEM private key"
            ) from exc
        
        self.public_key = base64.b64encode(
            self.private_key.public_key().public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        ).decode("utf-8")

        if "HMZ_AUTH_HOSTNAME" not in os.environ:
            raise errors.ConfigError("HMZ_AUTH_HOSTNAME not found")
        self.hmz_auth_hostname = os.environ["HMZ_AUTH_HOSTNAME"]

        if "HMZ_AUTH_PATH" not in os.environ:
            raise errors.ConfigError("HMZ_AUTH_PATH not found")
        self.hmz_auth_path = os.environ["HMZ_AUTH_PATH"]

        if "HMZ_AUTH_CUSTOMERID" not in os.environ:
            raise errors.ConfigError("HMZ_AUTH_CUSTOMERID not found")
        self.hmz_auth_customerid = os.environ["HMZ_AUTH_CUSTOMERID"]

        if "HMZ_API_HOSTNAME" not in os.environ:
            raise errors.ConfigError("HMZ_API_HOSTNAME not found")
        self.hmz_api_hostname = os.environ["HMZ_API_HOSTNAME"]

        vaultids = os.environ.get("VAULTIDS") or os.environ.get("VAULTID")
        if not vaultids:
            raise errors.ConfigError("VAULTID or VAULTIDS not found")
        self.vaultids = vaultids.replace(",", " ").split()

        self.seed = os.environ.get("OSOENCRYPTIONPASS", "")
        self.batch_size = os.environ.get("BATCH_UPLOAD_SIZE", 20)

        self.root_cert_b64 = os.environ.get("ROOTCERT")
        with tempfile.NamedTemporaryFile(delete=False) as root_cert_file:
            self.verify = self._write_root_cert(root_cert_file)

        if "TOKEN_EXP" not in os.environ:
            raise errors.ConfigError("TOKEN_EXP not found")
        self.token_exp = os.environ.get("TOKEN_EXP")

        self.token_exp_in_secs = utils.parse_wait_time(self.token_exp)
        if self.token_exp_in_secs == 0:
            raise errors.ConfigError("TOKEN_EXP format is invalid")

        # Defaults retry each batch for >20 minutes total (linear backoff:
        try:
            self.broadcast_retries = int(os.environ.get("BROADCAST_RETRIES", 10))
            self.broadcast_retry_delay = float(
                os.environ.get("BROADCAST_RETRY_DELAY_SECS", 30)
            )
        except ValueError:
            raise errors.ConfigError(
                "BROADCAST_RETRIES and BROADCAST_RETRY_DELAY_SECS must be numeric"
            )
        if self.broadcast_retries < 1:
            raise errors.ConfigError("BROADCAST_RETRIES must be a positive integer")
        # (connect, read) timeouts for requests to the Ripple Custody API
        self.request_timeout = (10, 120)

        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()

    def _sign(self, challenge: str = str(uuid.uuid4())) -> bytes:
        """
        Sign the challenge string and then convert the signature into a DER format.

        Parameters:

            challenge (`str`):

                An unique challenge string.

        Returns:

            `bytes`:

                A DER encoded signature as a byte string.
        """
        if isinstance(self.private_key, ed25519.Ed25519PrivateKey):
            """
            An ED25519 signature produces a 64-byte sequence which has to be converted
            into the correct DER structure:

            0x30 : DER Composite structure header
            0x44 : length (68) of following payload
            0x02 : type of payload (int)
            0x20 : length (32) of (int) payload
                 : 32-byte length payload (r), first half of ``hexsig``
            0x02 : type of payload (int)
            0x20 : length (32) of (int) payload
                 : 32-byte length payload (s), second half of ``hexsig``
            """
            hexsig = self.private_key.sign(
                bytes(challenge, "utf-8"),
            ).hex()
            return bytes.fromhex("30440220" + hexsig[:64] + "0220" + hexsig[64:])

        elif isinstance(self.private_key, ec.EllipticCurvePrivateKey):
            return self.private_key.sign(
                data=bytes(challenge, "utf-8"),
                signature_algorithm=ec.ECDSA(hashes.SHA256()),
            )

        else:
            raise Exception(f"Key type not supported: {type(self.private_key)}")

    @lru_cache()  # Cache result - token + issue time + lifetime
    def _get_token(self) -> Tuple[str, float, float]:
        self.logger.info("Generating new JWT access token...")

        challenge = str(uuid.uuid4())
        signature = self._sign(challenge)

        data = {
            "client_id": self.hmz_auth_customerid,
            "grant_type": "password",
            "challenge": challenge,
            "public_key": self.public_key,
            "signature": base64.b64encode(signature).decode("utf-8"),
        }

        url = f"https://{self.hmz_auth_hostname}{self.hmz_auth_path}"

        try:
            response = self.session.post(
                url,
                data=data,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                verify=self.verify,
                timeout=self.request_timeout,
            )

        except requests.exceptions.Timeout as e:
            self.logger.error("Timeout while requesting token: %s", e)
            raise errors.NetworkError("Token request timeout") from e

        except requests.exceptions.ConnectionError as e:
            self.logger.error("Connection error while requesting token: %s", e)
            raise errors.NetworkError("Token connection error") from e

        except requests.exceptions.RequestException as e:
            self.logger.error("Unexpected network error: %s", e)
            raise errors.NetworkError("Unexpected token request error") from e

        if response.status_code in (401, 403):
            self.logger.error(
                "Authentication failed with status %s: %s",
                response.status_code,
                response.text,
            )
            raise errors.AuthenticationError("Authentication failed")

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self.logger.error(
                "HTTP error while requesting token: %s - %s",
                response.status_code,
                response.text,
            )
            raise errors.TokenError(
                f"Token endpoint returned HTTP {response.status_code}"
            ) from e

        try:
            response_json = response.json()
        except ValueError as e:
            self.logger.error(
                "Invalid JSON returned from token endpoint: %s",
                response.text,
            )
            raise errors.TokenError("Invalid JSON response from token endpoint") from e

        token = response_json.get("access_token")
        if not token:
            self.logger.error(
                "No access_token in response: %s",
                response_json,
            )
            raise errors.TokenError("Could not get token from response")

        lifetime = float(self.token_exp_in_secs)
        expires_in = response_json.get("expires_in")
        if expires_in is not None:
            try:
                lifetime = min(float(expires_in), lifetime)
            except (TypeError, ValueError):
                self.logger.warning(f"Ignoring non-numeric expires_in: {expires_in}")

        self.logger.info("Successfully generated new JWT access token")

        return token, time.time() ,lifetime

    def _write_root_cert(self, root_cert_file: IO[bytes]) -> Union[str, bool]:
        if not self.root_cert_b64:
            self.logger.info("ROOTCERT not configured")
            return True
    
        try:
            rootcert = base64.b64decode(
                self.root_cert_b64,
                validate=True,
            )
        except Exception as exc:
            self.logger.error(
                "Failed to decode ROOTCERT: %s",
                exc,
            )
            raise errors.ConfigError(
                "ROOTCERT is not valid Base64"
            ) from exc
        
        try:
            root_cert_file.write(rootcert)
            root_cert_file.seek(0)
        except OSError as exc:
            self.logger.error(
                "Failed to write ROOTCERT to temporary file: %s",
                exc,
            )
            raise errors.ConfigError(
                "Failed to write ROOTCERT"
            ) from exc
    
        return root_cert_file.name

    def get_token(self) -> str:
        self.logger.info("Obtaining JWT access token...")
        token, issued_at, lifetime = self._get_token()
        buff = int(os.environ.get("TOKEN_EXP_BUFF", 10))
        if time.time() - issued_at > lifetime - buff:
            # token is (about to be) expired - generate a new one
            self._get_token.cache_clear()
            token, issued_at, lifetime = self._get_token()
        self.logger.info("Successfully obtained JWT access token")
        return token

    def bulk_download(self) -> list:
        self.logger.info("Performing bulk download from frontend")
        token = self.get_token()

        documents = []

        for vaultid in self.vaultids:
            url = f"https://{self.hmz_api_hostname}/v1/vaults/{vaultid}/operations/prepared"

            try:
                response = requests.get(
                    url=url,
                    headers={"Authorization": f"Bearer {token}"},
                    verify=self.verify,
                    timeout=self.request_timeout,
                )
            except requests.exceptions.RequestException as e:
                self.logger.error(
                    "Network error while downloading vault %s: %s",
                    vaultid,
                    str(e),
                )
                continue  # move to next vault

            if response.status_code == 401:
                 self.logger.warning("Download got HTTP 401; refreshing access token")
                 self._get_token.cache_clear()
                 token = self.get_token()
                 response = requests.get(
                    url=url,
                    headers={"Authorization": "Bearer " + token},
                    stream=True,
                    verify=self.verify,
                    timeout=self.request_timeout,
                 )

            status = response.status_code

            # ---- Handle non-success HTTP codes ----
            if not (200 <= status < 300):
                self.logger.error(
                    "Download rejected for vault %s: status=%s body=%s",
                    vaultid,
                    status,
                    response.text[:2000],  # prevent huge logs
                )
                continue  # move to next vault

            # ---- Handle 204 / empty response ----
            if status == 204 or not response.content:
                self.logger.info(
                    "No content returned for vault %s (status=%s)",
                    vaultid,
                    status,
                )
                continue

            # ---- Parse JSON safely ----
            try:
                vault_json = response.json()
            except ValueError:
                self.logger.error(
                    "Invalid JSON for vault %s: %s",
                    vaultid,
                    response.text[:2000],
                )
                continue

            self.logger.info(
                "Bulk download finished successfully for vault %s",
                vaultid,
            )

            empty_content = {
                "vaultId": vaultid,
                "accounts": [],
                "transactions": [],
                "manifests": [],
                "rewraps": [],
            }

            def write_document_set(documents, content_key: str, id_key: str):
                for item in vault_json.get(content_key, []):
                    try:
                        document_id = item.get(id_key)

                        if not document_id:
                            self.logger.warning(
                                "Missing %s in vault %s for %s",
                                id_key,
                                vaultid,
                                content_key,
                            )
                            continue

                        self.logger.info(
                            "Saving document %s from %s (vault %s)",
                            document_id,
                            content_key,
                            vaultid,
                        )

                        content = copy.deepcopy(empty_content)
                        content.setdefault(content_key, []).append(item)

                        # Encrypt content if seed provided
                        if self.seed:
                            for section in ["transactions", "manifests", "accounts", "rewraps"]:
                                for section_item in content.get(section, []):
                                    if "signedPayload" in section_item:
                                        section_item["signedPayloadCiphered"] = crypt.encrypt(
                                            section_item["signedPayload"],
                                            self.seed,
                                        )
                                        del section_item["signedPayload"]

                        data = json.dumps(content)
                        meta = {"source": vaultid, "type": content_key}

                        documents.append(
                            {
                                "id": document_id,
                                "content": data,
                                "metadata": json.dumps(meta),
                            }
                        )

                        self.logger.info(
                            "Successfully saved document %s (vault %s)",
                            document_id,
                            vaultid,
                        )

                    except Exception:
                        self.logger.exception(
                            "Failed processing document in vault %s (%s)",
                            vaultid,
                            content_key,
                        )
                        continue

            for content_key, id_key in [
                ("transactions", "transactionId"),
                ("accounts", "accountId"),
                ("manifests", "manifestId"),
                ("rewraps", "rewrapSecretMaterialsId"),
            ]:
                write_document_set(documents, content_key, id_key)

        return documents   

    def bulk_upload(self, documents):
        vaults = []
        transactions = []
        accounts = []
        manifests = []
        rewraps = []

        doc_count = 0
        batch_num = 1
        failed_batches = []  # track batches that failed to send

        self.logger.info("Saving documents for bulk upload")
        for document in documents:
            try:
                document_id = document["id"]

                self.logger.info(
                    "Processing document %s for bulk upload",
                    document_id,
                )

                contents = json.loads(document["content"])
                # Decrypt content
                if self.seed:
                    for section in ("transactions", "accounts", "manifests"):
                        for item in contents.get(section, []):
                            if "signedPayloadCiphered" in item:
                                item["signedPayload"] = crypt.decrypt(
                                    item["signedPayloadCiphered"],
                                    self.seed,
                                )
                                del item["signedPayloadCiphered"]

                transactions.extend(contents.get("transactions", []))
                accounts.extend(contents.get("accounts", []))
                manifests.extend(contents.get("manifests", []))
                vaults.extend(contents.get("vaults", []))
                rewraps.extend(contents.get("rewraps", []))

                doc_count += 1

                self.logger.info(
                    f"Successfully saved document {document_id} for bulk upload"
                )

            except Exception as e:
                # Only parsing/decryption failures land here
                # a bad document is skipped, batch state is untouched.
                self.logger.exception(e)
                continue

            # Flush every batch_size documents
            if doc_count >= self.batch_size:
                self.logger.info(f"Flushing batch {batch_num} ({doc_count} documents)")
                self._flush_batch(
                    batch_num, transactions, accounts, manifests, vaults, rewraps, failed_batches
                )
                vaults, transactions, accounts, manifests, rewraps, doc_count = [], [], [], [], [], 0
                batch_num += 1


        # Send any remaining documents
        if doc_count > 0:
            self.logger.info(f"Flushing final batch {batch_num} ({doc_count} documents)")
            self._flush_batch(
                batch_num, transactions, accounts, manifests, vaults, rewraps, failed_batches
            )

        if failed_batches:
            self.logger.error(
                f"Bulk upload finished with {len(failed_batches)} failed batch(es): "
                f"{failed_batches}"
            )
            raise errors.BroadcastError(
                f"{len(failed_batches)} of {batch_num} batch(es) failed to upload "
                f"after {self.broadcast_retries} attempt(s) each: {failed_batches}"
            )
        self.logger.info("Bulk upload finished successfully")

    def _flush_batch(self, batch_num, transactions, accounts, manifests, vaults, rewraps, failed_batches):
        """Send one batch; on failure, log it, record it, and let the run continue."""
        try:
            self._send_batch(transactions, accounts, manifests, vaults, rewraps)
        except Exception as e:
            self.logger.exception(f"Batch {batch_num} failed to upload: {e}")
            failed_batches.append({"batch_num": batch_num, "error": str(e)})

    def _is_retryable(self, response) -> bool:
        # 401: token may have expired mid-run; 429/5xx: transient on Ripple's side
        return response.status_code == 401 or response.status_code == 429 or response.status_code >= 500

    def _send_batch(self, transactions, accounts, manifests, vaults, rewraps):
        content = {
            "accounts": accounts,
            "transactions": transactions,
            "manifests": manifests,
            "vaults": vaults,
            "rewraps": rewraps,
        }

        self.logger.info(
            f"Performing bulk upload to frontend "
            f"(accounts={len(accounts)}, transactions={len(transactions)}, "
            f"manifests={len(manifests)}, vaults={len(vaults)})"
        )

        vault_file_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as vault_file:
                json.dump(content, vault_file)
                vault_file_path = vault_file.name
            last_error = None
            for attempt in range(1, self.broadcast_retries + 1):
                try:
                    token = self.get_token()
                    with open(vault_file_path, "rb") as f:
                        response = requests.post(
                            url=f"https://{self.hmz_api_hostname}/v1/vaults/operations/signed",
                            headers={"Authorization": "Bearer " + token},
                            files={"files": f},
                            verify=self.verify,
                            timeout=self.request_timeout,
                        )
                    if response.ok:
                        return
                    self.logger.warning(
                        f"Upload attempt {attempt}/{self.broadcast_retries} got "
                        f"HTTP {response.status_code}: {response.text[:500]}"
                    )
                    if response.status_code == 401:
                        self._get_token.cache_clear()
                    if not self._is_retryable(response):
                        response.raise_for_status()
                    last_error = requests.HTTPError(
                        f"HTTP {response.status_code}", response=response
                    )
                except (requests.ConnectionError, requests.Timeout) as e:
                    self.logger.warning(
                        f"Upload attempt {attempt}/{self.broadcast_retries} failed: "
                        f"{type(e).__name__}"
                    )
                    last_error = e
                if attempt < self.broadcast_retries:
                    time.sleep(self.broadcast_retry_delay * attempt)
            if last_error is None:
                last_error = errors.BroadcastError("upload failed with no response")
            raise last_error
        finally:
            if vault_file_path:
                os.remove(vault_file_path)


    def backend_status(self):
        pass
