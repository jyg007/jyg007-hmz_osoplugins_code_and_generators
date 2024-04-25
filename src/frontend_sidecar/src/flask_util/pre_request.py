#
# Licensed Materials - Property of IBM
#
# (c) Copyright IBM Corp. 2023
#
# The source code for this program is not published or otherwise
# divested of its trade secrets, irrespective of what has been
# deposited with the U.S. Copyright Office
#


import logging
import sys
import re

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes

from urllib.parse import unquote
from os import environ

from flask import Flask, request, request_started, abort

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


sha1_regex = re.compile(r'^[a-fA-F0-9]{40}$')


def is_sha1_hash(s):
    """Check if a string is a valid SHA-1 hash."""
    if re.match(sha1_regex, s):
        return True
    else:
        return False


def load_fingerprints():
    try:
        fingerprints = [f.upper()
                        for f in environ['COMPONENT_FINGERPRINTS'].split()]
    except KeyError as e:
        logger.info(
            'Could not find COMPONENT_FINGERPRINTS in environment variables')
        raise e

    for fingerprint in fingerprints:
        if not is_sha1_hash(fingerprint):
            logger.error(
                f'{fingerprint}, located in COMPONENT_FINGERPRINTS, is not a sha1 hash')
            raise Exception(f'{fingerprint}, located in COMPONENT_FINGERPRINTS, is not a sha1 hash')

    return fingerprint


def bind_flask_before_request(sender: Flask, **extras) -> None:
    logger.info(
        f"HTTP Method: {request.method} URL Path: {request.path}")

    client_verify = request.headers.get("X-SSL-CLIENT-VERIFY", "FAILED")
    if client_verify != "SUCCESS":
        logger.info(
            f'Could not verify certificate, client verify: {client_verify}')
        abort(401, {'error': {'code': '401', 'message': 'Unauthorized'}})

    if 'X-SSL-CERT' not in request.headers:
        sender.logger.info('[X-SSL-CERT] not in request header')
        abort(401, {'error': {'code': '401', 'message': 'Unauthorized'}})

    cert_bytes = unquote(request.headers['X-SSL-CERT']).encode('utf-8')
    x509_cert = x509.load_pem_x509_certificate(
        cert_bytes, default_backend())

    fingerprint = bytearray(x509_cert.fingerprint(hashes.SHA1())).hex()
    logger.info(f'Fingerprint: {fingerprint}')

    user = x509_cert.subject.rfc4514_string()
    logger.info(f'User: {user}')
    logger.info("AUTHENTICATED")

    if not fingerprint:
        logger.info(
            'Fingerprint for client cert was not generated')
        abort(
            403, {'error': {'code': '403', 'message': 'Forbidden'}})

    if fingerprint.upper() not in authorized_fingerprints:
        logger.info(
            f'Could not find fingerprint {fingerprint} in COMPONENT_FINGERPRINTS')
        abort(
            403, {'error': {'code': '403', 'message': 'Forbidden'}})


def configure_flask_common(app: Flask) -> None:
    global authorized_fingerprints
    authorized_fingerprints = load_fingerprints()
    request_started.connect(bind_flask_before_request, app)
