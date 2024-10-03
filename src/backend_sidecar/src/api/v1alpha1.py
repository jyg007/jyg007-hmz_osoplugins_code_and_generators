# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import os

import consts
from flask import request
from flask_restx import Namespace, Resource, fields

from backend_sidecar import (backend_status, bulk_download, bulk_upload,
                             save_documents)

api = Namespace("v1alpha1", description="")

content_model = api.model(
    "Harmonize_Document_Content",
    {
        "vaultId": fields.String(),
        "transactions": fields.List(fields.Strings()),
        "accounts": fields.List(fields.Strings()),
        "manifests": fields.List(fields.Strings()),
    },
)


document_model = api.model(
    "Document",
    {
        "id": fields.String(),
        "content": fields.Nested(content_model),
        "signature": fields.String(),
    },
)

documents_model = api.model(
    "Documents",
    {
        "documents": fields.List(fields.Nested(document_model)),
        "count": fields.Integer(),
    },
)

component_status_model = api.model(
    "ComponentStatus", {"status": fields.String(), "error": fields.String()}
)


@api.route("/documents", methods=["POST"])
class Upload(Resource):
    @api.doc(
        summary="Upload a batch of confirmed documents",
        description=(
            "This endpoint enables the offline signing coductor's input bridge"
            " service to upload multiple signed documents to the backend"
        ),
        operationId="backendBatchUpload",
        body=documents_model,
    )
    @api.response(code=200, description="Documents batched and forwarded as response")
    def post(self):
        save_documents(request.get_json(force=True)["documents"])
        bulk_upload()
        return "OK", 200


@api.route("/documents", methods=["GET"])
class Download(Resource):
    @api.doc(
        summary="Download a batch of signed documents",
        description="GET",
        operationId="backendBatchDownload",
        model=documents_model,
    )
    @api.response(code=200, description="", model=documents_model)
    def get(self):
        os.makedirs(consts.SIGNED_DIR, exist_ok=True)
        documents = bulk_download()
        return {"documents": documents, "count": len(documents)}


@api.route("/status", methods=["GET"])
class Status(Resource):
    @api.response(code=200, description="", model=component_status_model)
    @api.response(code=503, description="", model=component_status_model)
    def get(self):
        response, status_code = backend_status()
        return {"status": response}, status_code
