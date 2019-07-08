from flask import Flask
from flask import jsonify, abort
from merkle_drop.airdrop import get_item, to_items, get_balance
from merkle_drop.merkle_tree import create_proof, build_tree
from merkle_drop.load_csv import load_airdrop_file
from eth_utils import encode_hex, is_checksum_address, to_canonical_address
import configparser
import time
import math

config = configparser.ConfigParser()
config.read("config.ini")

airdrop_dict = load_airdrop_file(config.get("trustlines.merkle", "AirdropFileName"))
airdrop_tree = build_tree(to_items(airdrop_dict))
decay_start_time = int(config.get("trustlines.merkle", "DecayStartTime"))
decay_duration_in_seconds = int(
    config.get("trustlines.merkle", "DecayDurationInSeconds")
)

app = Flask("Merkle Airdrop Backend Server")


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
    decayed_tokens = decay_tokens(eligible_tokens)
    return jsonify(
        {
            "address": address,
            "originalTokenBalance": eligible_tokens,
            "currentTokenBalance": decayed_tokens,
            "proof": [encode_hex(hash_) for hash_ in proof],
        }
    )


# See also MerkleDrop.sol:61
def decay_tokens(tokens: int) -> int:
    now = int(time.time())
    if now <= decay_start_time:
        return tokens
    elif now >= decay_start_time + decay_duration_in_seconds:
        return 0
    else:
        time_decayed = now - decay_start_time
        decay = math.ceil(tokens * time_decayed / decay_duration_in_seconds)
        assert(tokens <= decay)
        return tokens - decay


if __name__ == "__main__":
    app.run(host=config.get("flask", "Host"), port=int(config.get("flask", "Port")))
