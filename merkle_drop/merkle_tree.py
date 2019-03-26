from typing import Dict, List, Optional
from eth_utils import keccak, is_canonical_address


class Tree:
    def __init__(self, root, leaves: List["Node"]):
        self.root = root
        self.leaves = leaves


class Node:
    def __init__(
        self,
        hash: bytes,
        parent: "Node" = None,
        left_child: "Node" = None,
        right_child: "Node" = None,
    ):
        self.hash = hash
        self.parent = parent
        self.left_child = left_child
        self.right_child = right_child

    def __repr__(self):
        return f"Node({self.hash!r}, {self.parent!r}, {self.left_child!r}, {self.right_child!r})"


def compute_merkle_root(airdrop_list: list):

    return build_tree(airdrop_list).root.hash


def build_tree(address_value_dict: Dict[bytes, int]) -> Tree:

    current_nodes = leaves = _build_leaves(address_value_dict)
    next_nodes = []

    while len(current_nodes) > 1:

        for (node1, node2) in zip(current_nodes[0::2], current_nodes[1::2]):
            parent = Node(
                compute_parent_hash(node1.hash, node2.hash),
                left_child=node1,
                right_child=node2,
            )
            node1.parent = parent
            node2.parent = parent
            next_nodes.append(parent)

        if len(current_nodes) % 2 != 0:
            next_nodes.append(current_nodes[-1])

        current_nodes = next_nodes
        next_nodes = []

    tree = Tree(current_nodes[0], leaves)

    return tree


def compute_leaf_hash(address: bytes, value: int) -> bytes:
    if not is_canonical_address(address):
        raise ValueError("Address must be a canonical address")

    if value < 0 or value >= 2 ** 256:
        raise ValueError("value is negative or too large")

    return keccak(address + value.to_bytes(32, "big"))


def _build_leaves(address_value_dict: Dict[bytes, int]) -> List[Node]:
    sorted_addresses = sorted(address_value_dict.keys())
    hashes = [
        compute_leaf_hash(address, address_value_dict[address])
        for address in sorted_addresses
    ]
    return [Node(h) for h in hashes]


def compute_parent_hash(left_hash: bytes, right_hash: bytes) -> bytes:
    little_child_hash, big_child_hash = sorted((left_hash, right_hash))
    return keccak(little_child_hash + big_child_hash)


def in_tree(address: bytes, value: int, root: Optional[Node]) -> bool:

    if root is None:
        return False

    if root.hash == compute_leaf_hash(address, value):
        return True

    return in_tree(address, value, root.left_child) or in_tree(
        address, value, root.right_child
    )


def create_proof(address: bytes, value: int, tree: Tree):

    leaf_hash = compute_leaf_hash(address, value)
    leaf = next((leave for leave in tree.leaves if leave.hash == leaf_hash), None)

    proof = []

    if leaf is None:
        return None

    while leaf.parent is not None:
        parent = leaf.parent

        if parent.left_child == leaf:
            if parent.right_child is None:
                raise RuntimeError("Child should not be None in tree")

            proof.append(parent.right_child.hash)
        elif parent.right_child == leaf:
            if parent.left_child is None:
                raise RuntimeError("Child should not be None in tree")

            proof.append(parent.left_child.hash)
        else:
            raise RuntimeError("wrong leave")

        leaf = leaf.parent

    return proof


def validate_proof(address: bytes, value: int, proof: List[bytes], root_hash: bytes):

    hash = compute_leaf_hash(address, value)

    for h in proof:
        hash = compute_parent_hash(hash, h)

    return hash == root_hash
