
import requests
import os
from datetime import datetime, timedelta
import uuid


def get_access_token():
    url = "https://api-pix.gerencianet.com.br/oauth/token"
    client_id = os.getenv("GERENCIANET_CLIENT_ID")
    client_secret = os.getenv("GERENCIANET_CLIENT_SECRET")

    response = requests.post(
        url,
        auth=(client_id, client_secret),
        headers={"Content-Type": "application/json"},
        json={"grant_type": "client_credentials"}
    )
    return response.json().get("access_token")


def create_pix_charge(value, client_name, txid=None):
    if not txid:
        txid = str(uuid.uuid4())[:35]

    access_token = get_access_token()
    vencimento = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "calendario": {"expiracao": 3600 * 24 * 3},
        "devedor": {"nome": client_name},
        "valor": {"original": f"{value:.2f}"},
        "chave": os.getenv("PIX_KEY"),
        "solicitacaoPagador": "Cobrança de serviço"
    }

    response = requests.put(
        f"https://api-pix.gerencianet.com.br/v2/cob/{txid}",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json=payload,
        cert=(os.getenv("CERT_PATH"), os.getenv("KEY_PATH"))
    )

    if response.status_code == 200:
        qr_response = requests.post(
            f"https://api-pix.gerencianet.com.br/v2/loc/{response.json()['loc']['id']}/qrcode",
            headers={"Authorization": f"Bearer {access_token}"},
            cert=(os.getenv("CERT_PATH"), os.getenv("KEY_PATH"))
        )
        qr_data = qr_response.json()
        return {
            "txid": txid,
            "valor": value,
            "qr_code": qr_data.get("imagemQrcode"),
            "br_code": qr_data.get("qrcode"),
            "vencimento": vencimento
        }
    else:
        return {"error": response.json()}

# encoding: utf-8

from efipay import EfiPay

credentials = {
    'client_id': 'client_id',
    'client_secret': 'client_secret',
    'sandbox': True,
    'certificate': 'insira-o-caminho-completo-do-certificado'
}

efi = EfiPay(credentials)

body = {
    'calendario': {
        'expiracao': 3600
    },
    'devedor': {
        'cpf': '12345678909',
        'nome': 'Francisco da Silva'
    },
    'valor': {
        'original': '123.45'
    },
    'chave': '71cdf9ba-c695-4e3c-b010-abb521a3f1be',
    'solicitacaoPagador': 'Cobrança dos serviços prestados.'
}

response =  efi.pix_create_immediate_charge(body=body)
print(response)
