
from flask import Flask, request, jsonify
from models import atualizar_status_cobranca_por_txid
from gerencianet_api import create_pix_charge
from models import save_charge #, get_charges

app = Flask(__name__)


@app.route("/create_charge", methods=["POST"])
def create_charge():
    try:
        data = request.json
        print("Dados recebidos no create_charge:", data)
        uid = data["uid"]
        value = float(data["value"])
        name = data["name"]
        desc_cobranca = data["solicitacaoPagador"]
        identificador = data["cpf"]
        id_token = data.get("id_token")
        cliente_id = data["cliente_id"]
        charge = create_pix_charge(value, name, desc_cobranca, identificador)
        print("Retorno da cobrança do Gerencianet:", charge)
        if charge.get("status") == "ATIVA" and "txid" in charge:
            status_code, response = save_charge(uid, cliente_id, charge)
            print("Resposta do Firestore:", status_code, response)
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
        data = request.get_json()
        print("[WEBHOOK] Dados recebidos:", data)

        pix = data.get("pix", [])
        if not pix:
            return jsonify({"mensagem": "Sem dados de pagamento."}), 200

        for evento in pix:
            txid = evento.get("txid")
            valor = evento.get("valor")
            horario = evento.get("horario")
            print(f"[WEBHOOK] Pagamento recebido: TXID={txid} | Valor={valor} | Horário={horario}")

            if txid:
                sucesso = atualizar_status_cobranca_por_txid(txid, novo_status="pago")
                if not sucesso:
                    print(f"[WEBHOOK] Não foi possível atualizar cobrança com TXID: {txid}")
            else:
                print("[WEBHOOK] Evento sem txid.")

        return jsonify({"mensagem": "Webhook processado com sucesso."}), 200

    except Exception as e:
        print("Erro no webhook:", e)
        return jsonify({"error": "Erro interno no servidor", "detalhes": str(e)}), 500


if __name__ == "__main__":
    from os import environ
    app.run(debug=True, host="0.0.0.0", port=int(environ.get("PORT", 5000)))
