import logging
import math
import time

import pendulum
from eth_utils import encode_hex, is_address, to_canonical_address, to_checksum_address
from flask import Flask, abort, jsonify
from flask_cors import CORS

from merkle_drop.airdrop import get_balance, get_item, to_items
from merkle_drop.load_csv import load_airdrop_file
from merkle_drop.merkle_tree import build_tree, create_proof

app = Flask("Merkle Airdrop Backend Server")

airdrop_dict = None
airdrop_tree = None
decay_start_time = -1
decay_duration_in_seconds = -1


def init_gunicorn_logging():
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)


def init_cors(**kwargs):
    """enable CORS

see https://flask-cors.corydolphin.com/en/latest/api.html#extension
for allowed kwargs

The default is to allow '*', but one can pass
e.g. origins='http://example.com' to allow request from one domain
only."
"""
    CORS(app=app, **kwargs)


def init(
    airdrop_filename: str,
    decay_start_time_param: int,
    decay_duration_in_seconds_param: int,
):
    global airdrop_dict
    global airdrop_tree
    global decay_start_time
    global decay_duration_in_seconds
    decay_start = pendulum.from_timestamp(decay_start_time_param)
    decay_end = pendulum.from_timestamp(
        decay_start_time_param + decay_duration_in_seconds_param
    )

    app.logger.info(f"Initializing merkle tree from file {airdrop_filename}")
    app.logger.info(f"Decay from {decay_start} to {decay_end}")
    airdrop_dict = load_airdrop_file(airdrop_filename)
    app.logger.info(f"Building merkle tree from {len(airdrop_dict)} entries")
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
    if not is_address(address):
        abort(400, "The address is not in checksum-case or invalid")
    canonical_address = to_canonical_address(address)

    eligible_tokens = get_balance(canonical_address, airdrop_dict)
    if eligible_tokens == 0:
        proof = []
        decayed_tokens = 0
    else:
        proof = create_proof(get_item(canonical_address, airdrop_dict), airdrop_tree)
        decayed_tokens = decay_tokens(eligible_tokens)
    return jsonify(
        {
            "address": to_checksum_address(address),
            "originalTokenBalance": str(eligible_tokens),
            "currentTokenBalance": str(decayed_tokens),
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
        assert decay <= tokens
        return tokens - decay


# Only for testing
if __name__ == "__main__":
    init_cors(origins="*")
    init("airdrop.csv", int(time.time()), 63_072_000)
    app.run()
