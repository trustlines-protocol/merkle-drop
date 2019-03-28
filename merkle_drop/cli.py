import click

from eth_utils import encode_hex

from .airdrop import to_items
from .load_csv import load_airdrop_file
from .merkle_tree import compute_merkle_root


@click.group()
def main():
    pass


@main.command(short_help="Compute Merkle root")
@click.argument("airdrop_file_name")
def root(airdrop_file_name):

    airdrop_data = load_airdrop_file(airdrop_file_name)
    merkle_root = compute_merkle_root(to_items(airdrop_data))

    click.echo(f"The merkle root is: {encode_hex(merkle_root)}")
