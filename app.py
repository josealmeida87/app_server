
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from firebase_config import init_firebase
from gerencianet_api import create_pix_charge
from models import save_charge, get_charges
import os


load_dotenv()
app = Flask(__name__)
db = init_firebase()


@app.route("/create_charge", methods=["POST"])
def create_charge():
    data = request.json
    uid = data["uid"]
    value = float(data["value"])
    name = data["name"]
    charge = create_pix_charge(value, name)
    if "error" in charge:
        return jsonify(charge), 400
    save_charge(db, uid, charge)
    return jsonify(charge)


@app.route("/charges/<uid>", methods=["GET"])
def list_charges(uid):
    charges = get_charges(db, uid)
    return jsonify(charges)
