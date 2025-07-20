from flask import Flask, request, jsonify
from models import atualizar_status_cobranca_por_txid, save_charge #, get_charges
from gerencianet_api import create_pix_charge, registrar_webhook_pix
import ssl
import os

app = Flask(__name__)

def configure_ssl_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.verify_mode = ssl.CERT_REQUIRED
    efi_cert_path = os.getenv("EFI_PUBLIC_CERT_PATH")
    if not os.path.exists(efi_cert_path):
        raise Exception(f"Certificado público da Efí não encontrado em {efi_cert_path}")
    context.load_verify_locations(efi_cert_path)
    return context

@app.route("/create_charge", methods=["POST"])
def create_charge():
    try:
        data = request.json
        # print("Dados recebidos no create_charge:", data)
        uid = data["uid"]
        value = float(data["value"])
        name = data["name"]
        desc_cobranca = data["solicitacaoPagador"]
        identificador = data["cpf"]
        id_token = data.get("id_token")
        cliente_id = data["cliente_id"]
        charge = create_pix_charge(value, name, desc_cobranca, identificador)
        # print("Retorno da cobrança do Gerencianet:", charge)
        if charge.get("status") == "ATIVA" and "txid" in charge:
            status_code, response = save_charge(uid, cliente_id, charge)
            # print("Resposta do Firestore:", status_code, response)
            return jsonify({
                "mensagem": "Cobrança criada com sucesso",
                "txid": charge["txid"],
                "valor": charge["valor"],
                "status": charge["status"],
                "solicitacaoPagador": charge["solicitacaoPagador"],
                "br_code": charge["br_code"],
                "nome": charge["nome"],
                "qr_code_image": charge["qr_code_image"],
                "location": charge["location"],
                "vencimento": charge["vencimento"].isoformat()
            }), 201

        return jsonify(charge)

        # return jsonify({"error": "Falha ao criar cobrança", "detalhes": res}), 400

    except Exception as e:
        import traceback
        print("Erro interno:", traceback.format_exc())
        return jsonify({"error": "Erro interno do servidor", "detalhes": str(e)}), 500


# @app.route("/charges/<uid>", methods=["GET"])
# def list_charges(uid, id_token, cliente_id):
#     charges = get_charges(uid, id_token, cliente_id)
#     return jsonify(charges)


@app.route("/webhook/efi", methods=["POST"])
def efi_webhook():
    try:
        # No Render, HTTPS é gerenciado pelo proxy, mas validamos mTLS
        if not hasattr(request, 'socket') or not request.socket.authorized:
            print("[WEBHOOK] Requisição não autorizada (mTLS falhou)")
            return jsonify({"error": "Não autorizado"}), 401

        data = request.get_json()
        print("[WEBHOOK] Dados recebidos:", data)

        pix_events = data.get("pix", []) if isinstance(data.get("pix"), list) else [data.get("pix")] if data.get("pix") else []
        if not pix_events:
            print("[WEBHOOK] Sem eventos Pix no payload")
            return jsonify({"mensagem": "Sem dados de pagamento."}), 200

        for evento in pix_events:
            txid = evento.get("txid")
            valor = evento.get("valor")
            horario = evento.get("horario")
            status = evento.get("status", "DESCONHECIDO").upper()

            print(f"[WEBHOOK] Evento recebido: TXID={txid} | Valor={valor} | Status={status} | Horário={horario}")

            if txid:
                novo_status = "pago" if status == "CONCLUIDA" else status.lower()
                sucesso = atualizar_status_cobranca_por_txid(txid, novo_status=novo_status)
                if not sucesso:
                    print(f"[WEBHOOK] Falha ao atualizar cobrança com TXID: {txid}")
            else:
                print("[WEBHOOK] Evento sem txid.")

        return jsonify({"mensagem": "Webhook processado com sucesso."}), 200
    except Exception as e:
        import traceback
        print("[WEBHOOK] Erro no webhook:", traceback.format_exc())
        return jsonify({"error": "Erro interno no servidor", "detalhes": str(e)}), 500

@app.route("/configure_webhook", methods=["POST"])
def configure_webhook():
    try:
        success = registrar_webhook_pix()
        return jsonify({"mensagem": "Webhook configurado com sucesso" if success else "Falha ao configurar webhook"}), 200 if success else 500
    except Exception as e:
        print("[CONFIG WEBHOOK] Erro:", str(e))
        return jsonify({"error": "Erro ao configurar webhook", "detalhes": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Render usa porta 8080 por padrão
    if os.environ.get("FLASK_ENV") != "development":
        registrar_webhook_pix()  # Configura webhook na inicialização
    app.run(debug=os.environ.get("FLASK_ENV") == "development", host="0.0.0.0", port=port)
