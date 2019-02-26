import click

from .load_json import load_airdrop_dict
from .merkle_tree import compute_merkle_root


@click.group()
def main():
    pass


@main.command(short_help="Compute Merkle root")
@click.argument("airdrop_json_file")
def root(airdrop_json_file):

    airdrop_dict = load_airdrop_dict(airdrop_json_file)  # noqa F841

    # TODO: adapt this to pass the correct list to `merkle_tree.py` once it is capable of processing a list of
    #  addresses and balances and not only numbers.
    airdrop_list = [1, 2, 3, 4, 5, 6]
    merkle_root = compute_merkle_root(airdrop_list)

    click.echo(f"The merkle root is: {merkle_root}")
