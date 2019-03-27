from typing import Dict, List

from .merkle_tree import Item

AirdropData = Dict[bytes, int]


def to_items(airdrop_data: AirdropData) -> List[Item]:
    return [Item(address, value) for address, value in airdrop_data.items()]
