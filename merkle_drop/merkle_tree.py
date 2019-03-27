from typing import List, Optional
from eth_utils import keccak


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


def build_tree(values: List) -> Tree:

    values.sort()

    current_nodes = leaves = _build_leaves(values)
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


def _build_leaves(values: List) -> List[Node]:
    return [Node(keccak(value)) for value in values]


def compute_parent_hash(left_hash: bytes, right_hash: bytes) -> bytes:
    little_child_hash, big_child_hash = sorted((left_hash, right_hash))
    return keccak(little_child_hash + big_child_hash)


def in_tree(value, root: Optional[Node]) -> bool:

    if root is None:
        return False

    if root.hash == keccak(value):
        return True

    return in_tree(value, root.left_child) or in_tree(value, root.right_child)


def create_proof(value, tree: Tree):

    leave = next((leave for leave in tree.leaves if leave.hash == keccak(value)), None)

    proof = []

    if leave is None:
        return None

    while leave.parent is not None:
        parent = leave.parent

        if parent.left_child == leave:
            if parent.right_child is None:
                raise RuntimeError("Child should not be None in tree")

            proof.append(parent.right_child.hash)
        elif parent.right_child == leave:
            if parent.left_child is None:
                raise RuntimeError("Child should not be None in tree")

            proof.append(parent.left_child.hash)
        else:
            raise RuntimeError("wrong leave")

        leave = leave.parent

    return proof


def validate_proof(value, proof: List[bytes], root_hash: bytes):

    hash = keccak(value)

    for h in proof:
        hash = compute_parent_hash(hash, h)

    return hash == root_hash
