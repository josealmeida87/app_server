import json
import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
load_dotenv()
if not firebase_admin._apps:
    # Inicialize com a conta de serviço
    cred_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
    if cred_json:
        cred_dict = json.loads(cred_json)
        cred = credentials.Certificate(cred_dict)
    else:
        # Ou tente carregar de arquivo físico
        cred = credentials.Certificate("firebase_admin.json")
    
    firebase_admin.initialize_app(cred)
    
db = firestore.client()

def save_charge(uid, cliente_id, charge_data):
    txid = charge_data["txid"]
    payload = db.collection("meus_clientes").document(uid)\
                .collection("clientes_do_usuario").document(cliente_id)\
                .collection("cobrancas").document(txid)
    payload.set({
        "uid": uid,
        "txid": txid,
        "valor": charge_data["valor"],
        "status": "pendente",
        "solicitacaoPagador": charge_data["solicitacaoPagador"],
        "nome": charge_data["nome"],
        "qr_code_image": charge_data["qr_code_image"],
        "br_code": charge_data["br_code"],
        "vencimento": charge_data["vencimento"],
        "created_at": datetime.utcnow()
    })

    return 200, {"message": "Salvo com sucesso"}


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


def registrar_webhook_pix():
    access_token = get_access_token()
    # url = "https://pix.api.efipay.com.br/v2/webhook/pix"
    url = "https://pix-h.api.efipay.com.br/v2/webhook/pix"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "x-skip-mtls-checking": "false"
    }
    payload = {
        "webhookUrl": os.getenv("WEBHOOK_URL", "api_base/webhook/efi"),
        "chave": os.getenv("PIX_KEY")
    }
    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            cert=efi_p12_path
        )
        if response.status_code == 201:
            print("[CONFIG WEBHOOK] Webhook configurado com sucesso:", response.json())
            return True
        else:
            print("[CONFIG WEBHOOK] Falha ao configurar webhook:", response.status_code, response.text)
            return False
    except Exception as e:
        print("[CONFIG WEBHOOK] Erro ao configurar webhook:", str(e))
        return False
