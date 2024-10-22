# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import sys
from os.path import isfile

from flask import request
from flask_restx import Namespace, Resource, fields

from oso_harmonize_plugins.frontend_plugin.frontend_plugin import (bulk_download,
                                                                   bulk_upload,
                                                                   backend_status)

import oso_harmonize_plugins.frontend_plugin.consts as consts

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

api = Namespace("v1alpha1", description="")

document_model = api.model(
    "Document",
    {"id": fields.String(), "content": fields.String(), "signature": fields.String()},
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


@api.route("/documents")
class Download(Resource):
    @api.doc(
        summary="Get prepared documents",
        description="This API downloads file from frontend.",
        operationId="pluginGetPrepared",
    )
    def get(self):
        confirmed_files = []
        data_dir, err = bulk_download()
        if err:
            logger.error(f"Could not complete bulk download, Error: {err}")
            return 500

        for filename in os.listdir(data_dir):
            filepath = os.path.join(data_dir, filename)
            if isfile(filepath):
                with open(filepath, "r") as f:
                    contents = f.read()
                    confirmed_files.append(
                        {"id": filename, "content": contents, "metadata": ""}
                    )
                os.remove(filepath)

        return {"documents": confirmed_files, "count": len(confirmed_files)}


@api.route("/documents")
class Upload(Resource):
    @api.doc(
        summary="Post signed documents",
        description="This API uploads file to frontend.",
        operationId="pluginPostSigned",
    )
    @api.response(code=200, description="Success")
    def post(self):
        json = request.get_json(force=True)
        os.makedirs(consts.SIGNED_DIR, exist_ok=True)
        for document in json["documents"]:
            filepath = os.path.join(consts.SIGNED_DIR, document["id"])
            logger.info("Saving document to {}".format(filepath))
            with open(filepath, "w") as f:
                f.write(document["content"])
        err = bulk_upload()
        if err:
            logger.error(err)
            return 500
        return "OK", 204


@api.route("/status")
class Status(Resource):
    def get(self):
        response, status_code = backend_status()
        return {"status": response}, status_code
