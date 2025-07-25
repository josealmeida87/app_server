import requests
import os
from datetime import datetime, timedelta
import uuid
import tempfile
from dotenv import load_dotenv
load_dotenv()

# cert_data = os.environ.get("CERT_PATH")
# key_data = os.environ.get("KEY_PATH")
cert_data = os.environ.get("SANDBOX_CERT_PATH")
key_data = os.environ.get("SANDBOX_KEY_PATH")
if not cert_data or not key_data:
    raise Exception("Certificados não encontrados nas variáveis de ambiente")

# Cria arquivos temporários com os certificados
cert_temp = tempfile.NamedTemporaryFile(delete=False)
key_temp = tempfile.NamedTemporaryFile(delete=False)
cert_temp.write(cert_data.encode())
key_temp.write(key_data.encode())
cert_temp.close()
key_temp.close()

def get_access_token():
    # client_id = os.getenv("CLIENT_ID")
    # client_secret = os.getenv("CLIENT_SECRET")
    client_id = os.getenv("SANDBOX_CLIENT_ID")
    client_secret = os.getenv("SANDBOX_CLIENT_SECRET")
    # url = "https://pix.api.efipay.com.br/oauth/token"
    url = "https://pix-h.api.efipay.com.br/oauth/token"
    cert = (cert_temp.name, key_temp.name)
    response = requests.post(
        url, 
        auth=(client_id, client_secret),
        headers={"Authorization": "Basic <base64_client_id_client_secret>"},
        data={"grant_type": "client_credentials"},
        cert=cert
    )
    return response.json()["access_token"]


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
        # response = requests.put(
        #     f"https://pix.api.efipay.com.br/v2/cob/{txid}",
        #     headers={
        #         "Authorization": f"Bearer {access_token}",
        #         "Content-Type": "application/json"
        #     },
        #     json=payload,
        #     cert=(cert_temp.name, key_temp.name)
        # )
        response = requests.put(
            f"https://pix-h.api.efipay.com.br/v2/cob/{txid}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            },
            json=payload,
            cert=(cert_temp.name, key_temp.name)
        )
        data_res = response.json()
        if response.status_code != 201:
            return {
                "error": "Falha ao criar cobrança",
                "status": response.status_code,
                "detalhes": response.json()
            }
        # qr_response = requests.get(
        #     f"https://pix.api.efipay.com.br/v2/loc/{data_res['loc']['id']}/qrcode",
        #     headers={"Authorization": f"Bearer {access_token}"},
        #     cert=(cert_temp.name, key_temp.name)
        # )
        qr_response = requests.get(
            f"https://pix-h.api.efipay.com.br/v2/loc/{data_res['loc']['id']}/qrcode",
            headers={"Authorization": f"Bearer {access_token}"},
            cert=(cert_temp.name, key_temp.name)
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
            "solicitacaoPagador": cobranca,
            "status": data_res.get("status"),
            "br_code": qr_data.get("qrcode"),
            "qr_code_image": qr_data.get("imagemQrcode"),
            "location": data_res.get("location"),
            "vencimento": datetime.now() + timedelta(days=3)
        }

    except Exception as e:
        return {"error": "Exceção durante a criação da cobrança", "detalhes": str(e)}


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

