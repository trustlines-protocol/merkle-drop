import pytest

from eth_utils import keccak

from merkle_drop.merkle_tree import (
    build_tree,
    in_tree,
    create_proof,
    validate_proof,
    compute_parent_hash,
    compute_leaf_hash,
    compute_merkle_root,
)


@pytest.fixture
def tree_data():
    return {
        b"\xaa" * 20: 1,
        b"\xbb" * 20: 2,
        b"\xcc" * 20: 3,
        b"\xdd" * 20: 4,
        b"\xee" * 20: 5,
    }


@pytest.fixture
def other_data():
    return {b"\xff" * 20: 6, b"\x00" * 20: 7}


@pytest.mark.parametrize(
    ("left_hash", "right_hash", "parent_hash"),
    [(b"\xaa", b"\xbb", keccak(b"\xaa\xbb")), (b"\xbb", b"\xaa", keccak(b"\xaa\xbb"))],
)
def test_parent_hash(left_hash, right_hash, parent_hash):
    assert compute_parent_hash(left_hash, right_hash) == parent_hash


@pytest.mark.parametrize(
    ("address", "value", "leaf_hash"),
    (
        (b"\xaa" * 20, 1, keccak(b"\xaa" * 20 + b"\x00" * 31 + b"\x01")),
        (b"\xbb" * 20, 255, keccak(b"\xbb" * 20 + b"\x00" * 31 + b"\xff")),
        (b"\xcc" * 20, 256, keccak(b"\xcc" * 20 + b"\x00" * 30 + b"\x01\x00")),
    ),
)
def test_leaf_hash(address, value, leaf_hash):
    assert compute_leaf_hash(address, value) == leaf_hash


def test_in_tree(tree_data):
    tree = build_tree(tree_data)

    assert all(
        in_tree(address, value, tree.root) for address, value in tree_data.items()
    )


def test_not_in_tree(tree_data, other_data):
    tree = build_tree(tree_data)

    assert not any(
        in_tree(address, value, tree.root) for address, value in other_data.items()
    )


def test_valid_proof(tree_data):
    tree = build_tree(tree_data)
    proofs = [
        create_proof(address, value, tree) for address, value in tree_data.items()
    ]

    assert all(
        validate_proof(address, value, proof, tree.root.hash)
        for (address, value), proof in zip(tree_data.items(), proofs)
    )


def test_invalid_proof(tree_data):
    tree = build_tree(tree_data)

    address, value = next(iter(tree_data.items()))
    assert not validate_proof(address, value, [], tree.root.hash)


def test_wrong_proof(tree_data):
    tree = build_tree(tree_data)
    proofs = [
        create_proof(address, value, tree) for address, value in tree_data.items()
    ]

    address, value = next(iter(tree_data.items()))
    assert not validate_proof(address, value, proofs[4], tree.root.hash)


def test_wrong_value(tree_data, other_data):
    tree = build_tree(tree_data)
    proofs = [
        create_proof(address, value, tree) for address, value in tree_data.items()
    ]

    address, value = next(iter(other_data.items()))
    assert not validate_proof(address, value, proofs[0], tree.root.hash)


def test_tree_is_sorted(tree_data):
    root = compute_merkle_root(tree_data)

    reversed_tree_data = dict(reversed(tuple(tree_data.items())))
    assert tuple(reversed_tree_data.keys()) != tuple(tree_data.keys())
    reversed_root = compute_merkle_root(reversed_tree_data)

    assert reversed_root == root
