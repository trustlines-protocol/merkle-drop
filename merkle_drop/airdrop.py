from typing import Dict, List, Union

from eth_utils import to_canonical_address

from .merkle_tree import Item

AirdropData = Dict[bytes, int]


def to_items(airdrop_data: AirdropData) -> List[Item]:
    return [Item(address, value) for address, value in airdrop_data.items()]


def get_balance(address: Union[str, bytes], airdrop_data: AirdropData) -> int:
    return airdrop_data.get(to_canonical_address(address), 0)
