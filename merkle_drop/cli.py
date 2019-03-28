import click

from eth_utils import encode_hex, is_checksum_address, to_canonical_address

from .airdrop import to_items, get_balance
from .load_csv import load_airdrop_file
from .merkle_tree import compute_merkle_root


def validate_address(ctx, param, value):
    if not is_checksum_address(value):
        raise click.BadParameter("Not a valid checksum address")
    return to_canonical_address(value)


@click.group()
def main():
    pass


@main.command(short_help="Compute Merkle root")
@click.argument("airdrop_file_name", type=click.Path(exists=True, dir_okay=False))
def root(airdrop_file_name):

    airdrop_data = load_airdrop_file(airdrop_file_name)
    merkle_root = compute_merkle_root(to_items(airdrop_data))

    click.echo(f"{encode_hex(merkle_root)}")


@main.command(short_help="Balance of address")
@click.argument("address", callback=validate_address)
@click.argument("airdrop_file_name", type=click.Path(exists=True, dir_okay=False))
def balance(address, airdrop_file_name):

    airdrop_data = load_airdrop_file(airdrop_file_name)
    balance = get_balance(address, airdrop_data)

    click.echo(f"{balance}")
