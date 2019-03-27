import click

from eth_utils import encode_hex

from .load_csv import load_airdrop_dict
from .merkle_tree import compute_merkle_root


@click.group()
def main():
    pass


@main.command(short_help="Compute Merkle root")
@click.argument("airdrop_json_file")
def root(airdrop_json_file):

    airdrop_dict = load_airdrop_dict(airdrop_json_file)  # noqa F841
    merkle_root = compute_merkle_root(airdrop_dict)

    click.echo(f"The merkle root is: {encode_hex(merkle_root)}")
