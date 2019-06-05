import pytest
import eth_tester

from merkle_drop.merkle_tree import (build_tree, Item, create_proof, validate_proof)

# increase eth_tester's GAS_LIMIT
assert eth_tester.backends.pyevm.main.GENESIS_GAS_LIMIT < 8 * 10 ** 6
eth_tester.backends.pyevm.main.GENESIS_GAS_LIMIT = 8 * 10 ** 6


@pytest.fixture(scope="session")
def tree_data():
    return [
        Item(b"\xaa" * 20, 1),
        Item(b"\xbb" * 20, 2),
        Item(b"\xcc" * 20, 3),
        Item(b"\xdd" * 20, 4),
        Item(b"\xee" * 20, 5),
    ]


@pytest.fixture(scope="session")
def other_data():
    return [Item(b"\xff" * 20, 6), Item(b"\x00" * 20, 7)]


@pytest.fixture(scope="session")
def proofs_for_tree_data(tree_data):
    tree = build_tree(tree_data)
    proofs = [create_proof(item, tree) for item in tree_data]


    assert all(
        validate_proof(item, proof, tree.root.hash)
        for item, proof in zip(tree_data, proofs)
    )

    return proofs


@pytest.fixture(scope="session")
def root_hash_for_tree_data(tree_data):
    tree = build_tree(tree_data)
    return tree.root.hash


@pytest.fixture(scope="session")
def merkle_drop_contract(deploy_contract, web3, root_hash_for_tree_data):
    contract = deploy_contract(
        "MerkleDrop",
        constructor_args=(root_hash_for_tree_data,)
    )

    return contract
