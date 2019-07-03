from flask import Flask
from flask import jsonify, abort
from typing import Dict
from .airdrop import get_item, to_items, get_balance
from .merkle_tree import create_proof, build_tree
from eth_utils import encode_hex, is_checksum_address, to_canonical_address

app = Flask("Merkle Airdrop Backend Server")
airdrop_dict = None
airdrop_tree = None


@app.errorhandler(404)
def not_found(e):
    return jsonify(error=404, message="Not found"), 404


@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=400, message=e.description), 400


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error=500, message="There was an internal server error"), 500


@app.route("/airdrop/<string:address>", methods=["GET"])
def get_airdrop_for(address):
    if not is_checksum_address(address):
        abort(400, "The address is not in checksum-case or invalid")
    canonical_address = to_canonical_address(address)

    eligible_tokens = get_balance(canonical_address, airdrop_dict)
    if eligible_tokens == 0:
        abort(404)
    proof = create_proof(get_item(canonical_address, airdrop_dict), airdrop_tree)
    # TODO: apply decay function on tokens
    return jsonify(
        {
            "address": address,
            "eligible_token_balance": eligible_tokens,
            "proof": [encode_hex(hash_) for hash_ in proof],
        }
    )


def start_server(airdrop_data: Dict[bytes, int], hostname: str, port: int) -> None:
    global airdrop_dict
    airdrop_dict = airdrop_data
    global airdrop_tree
    airdrop_tree = build_tree(to_items(airdrop_dict))
    app.run(host=hostname, port=port)
