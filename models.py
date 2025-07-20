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


def atualizar_status_cobranca_por_txid(txid, novo_status="pago"):
    print(f"[WEBHOOK] Atualizando txid {txid} para status '{novo_status}'")
    try:
        query = db.collection_group("cobrancas").where("txid", "==", txid).limit(1)
        docs = query.stream()
        
        atualizado = False
        for doc in docs:
            doc_ref = doc.reference
            doc_ref.update({"status": novo_status})
            print(f"[WEBHOOK] Status atualizado com sucesso para '{novo_status}' em {doc_ref.path}")
            atualizado = True
        
        if not atualizado:
            print(f"[WEBHOOK] Nenhum documento encontrado com txid: {txid}")
        return atualizado
    except Exception as e:
        print(f"[WEBHOOK] Erro ao atualizar status: {str(e)}")
        return False
