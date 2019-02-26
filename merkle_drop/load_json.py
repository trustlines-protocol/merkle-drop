import json


def load_airdrop_dict(airdrop_file: str):

    with open(airdrop_file) as file:
        airdrop_dict = json.load(file)

    return airdrop_dict
