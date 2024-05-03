# Copyright IBM Corp. All Rights Reserved.
#
# SPDX-License-Identifier: Apache-2.0

import os
import consts,json
import requests
import rest_client

def save_documents(documents, to_dir=consts.PREPARED_DIR):
    os.makedirs(to_dir, exist_ok=True)
    for document in documents:
        filepath = os.path.join(to_dir, document['id'])
        with open(filepath, 'w') as f:
            f.write(document["content"])

def bulk_upload(from_dir=consts.PREPARED_DIR):
    v_tx= []
    v_ac= []
    v_ma= []

    for filename in os.listdir(from_dir):
        filepath = os.path.join(from_dir, filename)
        f_j=open(filepath, 'r')
        jcontents = json.load(f_j)
        for i in jcontents["transactions"]:
            v_tx.append(i)
        for i in jcontents["accounts"]:
            v_ac.append(i)
        for i in jcontents["manifests"]:
            v_ma.append(i)
        os.remove(filepath)
        f_j.close

    try: 
      content = { "vaultId" : jcontents["vaultId"] , "accounts" : v_ac , "transactions" :  v_tx  , "manifests": v_ma }
    except:
      return

    filepath = os.path.join(consts.PREPARED_DIR, jcontents["vaultId"])

    with open(filepath, 'w') as outfile:
        json.dump(content,outfile)

    files = {'files': (jcontents["vaultId"], open(filepath, 'rb'))}

    response = requests.post(rest_client.get_backend_endpoint()+"/v1/feed/upload", files=files)

def bulk_download(to_dir=consts.SIGNED_DIR):
    documents = []

    response = requests.get(rest_client.get_backend_endpoint()+"/v1/feed/download?clean=True")

    jcontents = json.loads(response.text)
    for i in jcontents["transactions"]:
        content = {  "accounts" : [] , "transactions" : [ i ] , "manifests": [], "vaults": []}
        filepath = os.path.join(to_dir,i["transactionId"])
        with open(filepath, 'w') as outfile:
            json.dump(content,outfile)
    for i in jcontents["accounts"]:
        content = {  "accounts" : [ i ] , "transactions" : [  ] , "manifests": [], "vaults": [] }
        filepath = os.path.join(to_dir,i["accountId"])
        with open(filepath, 'w') as outfile:
            json.dump(content,outfile)
    for i in jcontents["manifests"]:
        content = {  "accounts" : [  ] , "transactions" : [  ] , "manifests": [ i ], "vaults": [] }
        filepath = os.path.join(to_dir,i["manifestId"])
        with open(filepath, 'w') as outfile:
            json.dump(content,outfile)
#    for i in jcontents["vaults"]:
#        content = {  "accounts" : [  ] , "transactions" : [  ] , "manifests": [  ], "vaults": [ i ] }
#        filepath = os.path.join(to_dir,i["vaultId"])
#        with open(filepath, 'w') as outfile:
#            json.dump(content,outfile)

    for filename in os.listdir(to_dir):
        filepath = os.path.join(to_dir, filename)
        with open(filepath, 'r') as f:
            documents.append({ 'id': filename, 'content': f.read(), 'metadata': "" })
        os.remove(filepath)
    return documents

def backend_status():
    return rest_client.status()

