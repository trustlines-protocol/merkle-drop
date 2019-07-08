from flask import Flask
from flask import jsonify, abort
from merkle_drop.airdrop import get_item, get_balance
from merkle_drop.merkle_tree import create_proof
from eth_utils import encode_hex, is_checksum_address, to_canonical_address
import time
import math
from merkle_drop.load_csv import load_airdrop_file
from merkle_drop.merkle_tree import create_proof, build_tree
from merkle_drop.airdrop import to_items

app = Flask("Merkle Airdrop Backend Server")


def init(airdrop_filename: str, decay_start_time_param: int, decay_duration_in_seconds_param: int):
    global airdrop_dict
    global airdrop_tree
    global decay_start_time
    global decay_duration_in_seconds
    airdrop_dict = load_airdrop_file(airdrop_filename)
    airdrop_tree = build_tree(to_items(airdrop_dict))
    decay_start_time = decay_start_time_param
    decay_duration_in_seconds = decay_duration_in_seconds_param


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
        assert(decay <= tokens)
        return tokens - decay
