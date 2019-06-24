import click

import pendulum
from eth_utils import encode_hex, is_checksum_address, to_canonical_address
from deploy_tools.cli import (
    jsonrpc_option,
    keystore_option,
    gas_option,
    gas_price_option,
    nonce_option,
    auto_nonce_option,
    connect_to_json_rpc,
    retrieve_private_key,
    get_nonce,
)
from deploy_tools.deploy import build_transaction_options

from .airdrop import get_item, to_items, get_balance
from .load_csv import load_airdrop_file
from .merkle_tree import compute_merkle_root, build_tree, create_proof
from .deploy import deploy_merkle_drop, sum_of_airdropped_tokens


def validate_address(ctx, param, value):
    if not is_checksum_address(value):
        raise click.BadParameter("Not a valid checksum address")
    return to_canonical_address(value)


def validate_date(ctx, param, value):
    if value is None:
        return None
    try:
        return pendulum.parse(value)
    except pendulum.parsing.exceptions.ParserError as e:
        raise click.BadParameter(
            f'The parameter "{value}" cannot be parsed as a date. (Try e.g. "2020-09-28", "2020-09-28T13:56")'
        ) from e


airdrop_file_argument = click.argument(
    "airdrop_file_name", type=click.Path(exists=True, dir_okay=False)
)


@click.group()
def main():
    pass


@main.command(short_help="Compute Merkle root")
@airdrop_file_argument
def root(airdrop_file_name: str) -> None:

    airdrop_data = load_airdrop_file(airdrop_file_name)
    merkle_root = compute_merkle_root(to_items(airdrop_data))

    click.echo(f"{encode_hex(merkle_root)}")


@main.command(short_help="Balance of address")
@click.argument("address", callback=validate_address)
@airdrop_file_argument
def balance(address: bytes, airdrop_file_name: str) -> None:

    airdrop_data = load_airdrop_file(airdrop_file_name)
    balance = get_balance(address, airdrop_data)

    click.echo(f"{balance}")


@main.command(short_help="Create Merkle proof for address")
@click.argument("address", callback=validate_address)
@airdrop_file_argument
def proof(address: bytes, airdrop_file_name: str) -> None:

    airdrop_data = load_airdrop_file(airdrop_file_name)
    proof = create_proof(
        get_item(address, airdrop_data), build_tree(to_items(airdrop_data))
    )

    click.echo(" ".join(encode_hex(hash_) for hash_ in proof))


@main.command(short_help="Deploy the MerkleDrop contract")
@keystore_option
@gas_option
@gas_price_option
@nonce_option
@auto_nonce_option
@jsonrpc_option
@click.option(
    "--token-address",
    help='The address of the airdropped token contract, "0x" prefixed string',
    type=str,
    required=True,
    callback=validate_address,
)
@click.option(
    "--airdrop-file",
    "airdrop_file_name",
    help="The path to the airdrop file containing the addresses and values to airdrop",
    type=click.Path(exists=True, dir_okay=False),
    required=True,
)
@click.option(
    "--decay-start-time",
    "decay_start_time",
    help="The start time for the decay of the tokens",
    type=int,
    required=False,
)
@click.option(
    "--decay-start-date",
    "decay_start_date",
    help='The start date for the decay of the tokens (e.g. "2020-09-28", "2020-09-28T13:56")',
    type=str,
    required=False,
    metavar="DATE",
    callback=validate_date,
)
@click.option(
    "--decay-duration",
    "decay_duration",
    help="The duration of the decay",
    type=int,
    required=False,
    default=63_072_000,  # two years in seconds
)
def deploy(
    keystore: str,
    jsonrpc: str,
    gas: int,
    gas_price: int,
    nonce: int,
    auto_nonce: bool,
    token_address: str,
    airdrop_file_name: str,
    decay_start_time: int,
    decay_start_date: pendulum.DateTime,
    decay_duration: int,
) -> None:

    if decay_start_date is not None and decay_start_time is not None:
        raise click.BadParameter(
            f"Both --decay-start-date and --decay-start-time have been specified"
        )
    if decay_start_date is None and decay_start_time is None:
        raise click.BadParameter(
            f"Please specify a decay start date with --decay-start-date or --decay-start-time"
        )

    if decay_start_date is not None:
        decay_start_time = int(decay_start_date.timestamp())

    web3 = connect_to_json_rpc(jsonrpc)
    private_key = retrieve_private_key(keystore)

    nonce = get_nonce(
        web3=web3, nonce=nonce, auto_nonce=auto_nonce, private_key=private_key
    )
    transaction_options = build_transaction_options(
        gas=gas, gas_price=gas_price, nonce=nonce
    )

    airdrop_data = load_airdrop_file(airdrop_file_name)
    airdrop_items = to_items(airdrop_data)
    merkle_root = compute_merkle_root(airdrop_items)

    constructor_args = (
        token_address,
        sum_of_airdropped_tokens(airdrop_items),
        merkle_root,
        decay_start_time,
        decay_duration,
    )

    merkle_drop = deploy_merkle_drop(
        web3=web3,
        transaction_options=transaction_options,
        private_key=private_key,
        constructor_args=constructor_args,
    )

    click.echo(f"MerkleDrop address: {merkle_drop.address}")
    click.echo(f"Merkle root: {encode_hex(merkle_root)}")
