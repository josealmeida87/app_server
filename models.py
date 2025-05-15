def save_charge(db, uid, charge_data):
    doc_ref = db.collection("charges").document(charge_data["txid"])
    doc_ref.set({
        "uid": uid,
        **charge_data,
        "status": "pendente"
    })

def get_charges(db, uid):
    charges = db.collection("charges").where("uid", "==", uid).stream()
    return [doc.to_dict() for doc in charges]
