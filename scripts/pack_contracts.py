"""This script takes an input contract.json and filters only the needed contracts
Usage: python pack_contracts.py input_contracts.json output_contracts.json
"""
import json

contracts = ["ERC20Interface", "MerkleDrop", "DroppedToken"]


def pack_contracts(input_filename, output_filename):
    with open(input_filename) as f:
        input_dict = json.load(f)

    output_dict = {}
    for contract in contracts:
        output_dict[contract] = input_dict[contract]

    with open(output_filename, "w") as f:
        json.dump(output_dict, f, indent=2)


if __name__ == "__main__":
    import sys

    pack_contracts(sys.argv[1], sys.argv[2])
