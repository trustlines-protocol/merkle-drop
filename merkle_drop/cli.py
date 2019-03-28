import click

from eth_utils import encode_hex, is_checksum_address, to_canonical_address

from .airdrop import get_item, to_items, get_balance
from .load_csv import load_airdrop_file
from .merkle_tree import compute_merkle_root, build_tree, create_proof


def validate_address(ctx, param, value):
    if not is_checksum_address(value):
        raise click.BadParameter("Not a valid checksum address")
    return to_canonical_address(value)


@click.group()
def main():
    pass


@main.command(short_help="Compute Merkle root")
@click.argument("airdrop_file_name", type=click.Path(exists=True, dir_okay=False))
def root(airdrop_file_name: str) -> None:

    airdrop_data = load_airdrop_file(airdrop_file_name)
    merkle_root = compute_merkle_root(to_items(airdrop_data))

    click.echo(f"{encode_hex(merkle_root)}")


@main.command(short_help="Balance of address")
@click.argument("address", callback=validate_address)
@click.argument("airdrop_file_name", type=click.Path(exists=True, dir_okay=False))
def balance(address: bytes, airdrop_file_name: str) -> None:

    airdrop_data = load_airdrop_file(airdrop_file_name)
    balance = get_balance(address, airdrop_data)

    click.echo(f"{balance}")


@main.command(short_help="Create merkle proof for address")
@click.argument("address", callback=validate_address)
@click.argument("airdrop_file_name", type=click.Path(exists=True, dir_okay=False))
def proof(address: bytes, airdrop_file_name: str) -> None:

    airdrop_data = load_airdrop_file(airdrop_file_name)
    proof = create_proof(
        get_item(address, airdrop_data), build_tree(to_items(airdrop_data))
    )

    click.echo(" ".join(encode_hex(hash_) for hash_ in proof))
