import requests
import os
from datetime import datetime, timedelta
import uuid
from dotenv import load_dotenv

load_dotenv()

cert_path = os.getenv(homol_certificate.pem)
key_path = os.getenv(homol_private_key.pem)


def get_access_token():
    url = "https://pix-h.api.efipay.com.br/oauth/token"
    client_id = os.getenv("SANDBOX_CLIENT_ID")
    client_secret = os.getenv("SANDBOX_CLIENT_SECRET")

    response = requests.post(
        url,
        auth=(client_id, client_secret),
        headers={"Content-Type": "application/json"},
        json={"grant_type": "client_credentials"},
        cert=(cert_path, key_path)
    )
    return response.json().get("access_token")


def create_pix_charge(value, client_name, cobranca, identificador=None, txid=None):
    global devedor
    if not txid:
        txid = uuid.uuid4().hex[:26]  # .hex remove os hífens e gera só letras/números

    access_token = get_access_token()
    vencimento = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "calendario": {
            "expiracao": 3600 * 24 * 3
        },
        "devedor": {
            "cpf": f"{identificador}",
            "nome": f"{client_name}"
        },
        "valor": {
            "original": f"{value:.2f}"
        },
        "chave": os.getenv("PIX_KEY"),
        "solicitacaoPagador": f"{cobranca}"
    }
    try:
        response = requests.put(
            f"https://pix-h.api.efipay.com.br/v2/cob/{txid}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=payload,
            cert=(os.getenv(cert_path), os.getenv(key_path))
        )
        data_res = response.json()
        if response.status_code != 201:
            return {
                "error": "Falha ao criar cobrança",
                "status": response.status_code,
                "detalhes": response.json()
            }
        qr_response = requests.get(
            f"https://pix-h.api.efipay.com.br/v2/loc/{data_res['loc']['id']}/qrcode",
            headers={"Authorization": f"Bearer {access_token}"},
            cert=(os.getenv(cert_path), os.getenv(key_path))
        )
        if qr_response.status_code != 200:
            return {
                "error": "Falha ao gerar QR Code",
                "status": qr_response.status_code,
                "detalhes": qr_response.json()
            }
        qr_data = qr_response.json()
        return {
            "txid": txid,
            "valor": value,
            "nome": client_name,
            "status": data_res.get("status"),
            "br_code": qr_data.get("qrcode"),
            "qr_code_image": qr_data.get("imagemQrcode"),
            "location": data_res.get("location"),
            "vencimento": datetime.now() + timedelta(days=3)
        }

    except Exception as e:
        return {"error": "Exceção durante a criação da cobrança", "detalhes": str(e)}
