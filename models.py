import json
import os
# import sys
import requests
from datetime import datetime
from dotenv import load_dotenv
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from firebase.firebase_auth import PROJECT_ID
load_dotenv()
project_id = os.getenv("PROJECT_ID")

def save_charge(uid, id_token, cliente_id, charge_data):
    txid = charge_data["txid"]
    url = (
        f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents"
        f"/meus_clientes/{uid}/clientes_do_usuario/{cliente_id}/cobrancas/{txid}"
    )

    payload = {
        "fields": {
            "uid": {"stringValue": uid},
            "txid": {"stringValue": txid},
            "valor": {"doubleValue": charge_data["valor"]},
            "status": {"stringValue": "pendente"},
            "nome": {"stringValue": charge_data["nome"]},
            "qr_code_image": {"stringValue": charge_data["qr_code_image"]},
            "br_code": {"stringValue": charge_data["br_code"]},
            "vencimento": {"timestampValue": charge_data["vencimento"].isoformat() + "Z"},
            "created_at": {"timestampValue": datetime.utcnow().isoformat() + "Z"}
        }
    }

    headers = {
        "Authorization": f"Bearer {id_token}",
        "Content-Type": "application/json"
    }

    response = requests.patch(url, headers=headers, json=payload)

    try:
        return response.status_code, response.json()
    except ValueError:
        return response.status_code, {"error": "Resposta vazia ou inválida", "text": response.text}


# def get_charges(uid, id_token, cliente_id):
#     base_url = (f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/"
#                 f"databases/(default)/documents/meus_clientes/{uid}/clientes_do_usuario/{cliente_id}/cobrancas")
#     headers = {"Authorization": f"Bearer {id_token}"}
#     res = requests.get(base_url, headers=headers)
#     data = res.json()
#
#     if res.status_code == 200:
#         charges = []
#         for doc in data.get("documents", []):
#             fields = doc.get("fields", {})
#             charges.append({
#                 "status": fields.get("status", {}).get("stringValue", "-"),
#                 "valor": fields.get("valor", {}).get("doubleValue", 0.0),
#                 "vencimento": fields.get("vencimento", {}).get("timestampValue", "")[:10],
#                 "nome": fields.get("nome", {}).get("stringValue", ""),
#                 "qr_code_image": fields.get("qr_code_image", {}).get("stringValue", ""),
#                 "br_code": fields.get("br_code", {}).get("stringValue", ""),
#                 "txid": fields.get("txid", {}).get("stringValue", "")
#             })
#         return charges
#     else:
#         return []


def atualizar_status_cobranca_por_txid(txid, novo_status="pago"):
    print(f"[WEBHOOK] Atualizando txid {txid} para status '{novo_status}'")
    url = f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents:runQuery"

    # Consulta Firestore com where txid == 'valor'
    payload = {
        "structuredQuery": {
            "from": [{"collectionId": "cobrancas"}],
            "where": {
                "fieldFilter": {
                    "field": {"fieldPath": "txid"},
                    "op": "EQUAL",
                    "value": {"stringValue": txid}
                }
            }
        }
    }

    headers = {"Content-Type": "application/json"}

    # 🔍 Realiza a consulta
    res = requests.post(url, headers=headers, data=json.dumps(payload))
    results = res.json()

    if res.status_code != 200:
        print("Erro ao consultar Firestore:", res.text)
        return False

    atualizado = False
    for result in results:
        doc = result.get("document")
        if not doc:
            continue

        doc_name = doc["name"]  # caminho completo do documento
        print(f"[WEBHOOK] Documento encontrado: {doc_name}")

        # 🔄 Atualiza o campo 'status'
        patch_payload = {
            "fields": {
                "status": {"stringValue": novo_status}
            }
        }
        patch_url = f"https://firestore.googleapis.com/v1/{doc_name}?updateMask.fieldPaths=status"
        patch_res = requests.patch(patch_url, headers=headers, json=patch_payload)

        if patch_res.status_code == 200:
            print(f"[WEBHOOK] Status atualizado com sucesso para '{novo_status}'")
            atualizado = True
        else:
            print("Erro ao atualizar status:", patch_res.text)

    return atualizado
