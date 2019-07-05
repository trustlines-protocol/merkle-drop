from flask import Flask
from flask import jsonify, abort
from typing import Dict
from merkle_drop.airdrop import get_item, to_items, get_balance
from merkle_drop.merkle_tree import create_proof, build_tree
from merkle_drop.load_csv import load_airdrop_file
from eth_utils import encode_hex, is_checksum_address, to_canonical_address
import configparser

config = configparser.ConfigParser()
config.read("config.ini")

app = Flask("Merkle Airdrop Backend Server")
airdrop_dict = load_airdrop_file(config["trustlines.merkle"]["AirdropFileName"])
airdrop_tree = build_tree(to_items(airdrop_dict))
decay_start_time = config["trustlines.merkle"]["DecayStartTime"]
decay_duration_in_seconds = config["trustlines.merkle"]["DecayDurationInSeconds"]


@app.errorhandler(404)
def not_found(e):
    return jsonify(error=404, message="Not found"), 404


@app.errorhandler(400)
def bad_request(e):
    return jsonify(error=400, message=e.description), 400


@app.errorhandler(500)
def internal_server_error(e):
    return jsonify(error=500, message="There was an internal server error"), 500


@app.route("/entitlement/<string:address>", methods=["GET"])
def get_entitlement_for(address):
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
            "originalTokenBalance": eligible_tokens,
            "proof": [encode_hex(hash_) for hash_ in proof],
        }
    )


if __name__ == "__main__":
    app.run(host=config["flask"]["Host"], port=config["flask"]["Port"])
