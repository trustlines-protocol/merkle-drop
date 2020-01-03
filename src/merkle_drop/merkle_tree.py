from typing import List, NamedTuple, Optional

from eth_utils import is_canonical_address, keccak


class Item(NamedTuple):
    address: bytes
    value: int


class Tree:
    def __init__(self, root, leaves: List["Node"]):
        self.root = root
        self.leaves = leaves


class Node:
    def __init__(
        self,
        hash: bytes,
        *,
        parent: "Node" = None,
        # left and right is arbitrary
        left_child: "Node" = None,
        right_child: "Node" = None,
    ):
        self.hash = hash
        self.parent = parent
        self.left_child = left_child
        self.right_child = right_child

    def __repr__(self):
        return f"Node({self.hash!r}, {self.parent!r}, {self.left_child!r}, {self.right_child!r})"


def compute_merkle_root(items: List[Item]):

    return build_tree(items).root.hash


def build_tree(items: List[Item]) -> Tree:

    current_nodes = leaves = _build_leaves(items)
    next_nodes = []

    while len(current_nodes) > 1:

        for (node1, node2) in zip(current_nodes[0::2], current_nodes[1::2]):
            parent = Node(
                compute_parent_hash(node1.hash, node2.hash),
                # left and right is arbitrary
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


def compute_leaf_hash(item: Item) -> bytes:
    address, value = item
    if not is_canonical_address(address):
        raise ValueError("Address must be a canonical address")

    if value < 0 or value >= 2 ** 256:
        raise ValueError("value is negative or too large")

    return keccak(address + value.to_bytes(32, "big"))


def _build_leaves(items: List[Item]) -> List[Node]:
    sorted_items = sorted(items)
    hashes = [compute_leaf_hash(item) for item in sorted_items]
    return [Node(h) for h in hashes]


def compute_parent_hash(left_hash: bytes, right_hash: bytes) -> bytes:
    little_child_hash, big_child_hash = sorted((left_hash, right_hash))
    return keccak(little_child_hash + big_child_hash)


def in_tree(item: Item, root: Node) -> bool:
    def _in_tree(item_hash: bytes, root: Optional[Node]) -> bool:

        if root is None:
            return False

        if root.hash == item_hash:
            return True

        return _in_tree(item_hash, root.left_child) or _in_tree(
            item_hash, root.right_child
        )

    return _in_tree(compute_leaf_hash(item), root)


def create_proof(item: Item, tree: Tree) -> List[bytes]:

    leaf_hash = compute_leaf_hash(item)
    leaf = next((leave for leave in tree.leaves if leave.hash == leaf_hash), None)

    proof = []

    if leaf is None:
        raise ValueError("Can not create proof for missing item")

    while leaf.parent is not None:
        parent = leaf.parent

        if parent.left_child == leaf:
            if parent.right_child is None:
                raise RuntimeError("Right child was none, invalid tree")

            proof.append(parent.right_child.hash)
        elif parent.right_child == leaf:
            if parent.left_child is None:
                raise RuntimeError("Left child was none, invalid tree")

            proof.append(parent.left_child.hash)
        else:
            raise RuntimeError("Item was not child of parent, invalid tree")

        leaf = leaf.parent

    return proof


def validate_proof(item: Item, proof: List[bytes], root_hash: bytes):

    hash = compute_leaf_hash(item)

    for h in proof:
        hash = compute_parent_hash(hash, h)

    return hash == root_hash
