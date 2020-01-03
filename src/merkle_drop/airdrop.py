from typing import Dict, List

from .merkle_tree import Item

AirdropData = Dict[bytes, int]


def get_item(address: bytes, airdrop_data: AirdropData) -> Item:
    return Item(address, airdrop_data[address])


def to_items(airdrop_data: AirdropData) -> List[Item]:
    return [Item(address, value) for address, value in airdrop_data.items()]


def get_balance(address: bytes, airdrop_data: AirdropData) -> int:
    return airdrop_data.get(address, 0)
