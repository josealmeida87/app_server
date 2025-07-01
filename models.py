import os
import sys
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# from firebase.firebase_auth import PROJECT_ID
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


def save_charge(uid, id_token, cliente_id, charge_data):
    project_id = os.getenv(PROJECT_ID)
    txid = charge_data["txid"]
    url = (f"https://firestore.googleapis.com/v1/projects/{project_id}"
           f"/databases/(default)/documents/meus_clientes/{uid}/clientes_do_usuario/{cliente_id}/cobrancas/{txid}")

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
    print(response)
    return response.status_code, response.json()


def get_charges(uid, id_token, cliente_id):
    base_url = (f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/"
                f"databases/(default)/documents/meus_clientes/{uid}/clientes_do_usuario/{cliente_id}/cobrancas")
    headers = {"Authorization": f"Bearer {id_token}"}
    res = requests.get(base_url, headers=headers)
    data = res.json()

    if res.status_code == 200:
        charges = []
        for doc in data.get("documents", []):
            fields = doc.get("fields", {})
            charges.append({
                "status": fields.get("status", {}).get("stringValue", "-"),
                "valor": fields.get("valor", {}).get("doubleValue", 0.0),
                "vencimento": fields.get("vencimento", {}).get("timestampValue", "")[:10],
                "nome": fields.get("nome", {}).get("stringValue", ""),
                "qr_code_image": fields.get("qr_code_image", {}).get("stringValue", ""),
                "br_code": fields.get("br_code", {}).get("stringValue", ""),
                "txid": fields.get("txid", {}).get("stringValue", "")
            })
        return charges
    else:
        return []


def atualizar_status_cobranca_por_txid(txid, novo_status="pago"):
    # Você precisará mapear o caminho do documento via txid
    # Exemplo: buscar cobranças por uid → filtrar por txid (ou salvar um índice local)
    print(f"[DEBUG] Webhook deseja atualizar txid {txid} para status '{novo_status}'")
    # Aqui você atualizaria o Firestore se tiver o UID e cliente_id mapeados

