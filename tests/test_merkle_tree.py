import pytest

from merkle_drop.merkle_tree import build_tree, in_tree, create_proof, validate_proof


@pytest.fixture
def tree_data():
    return [1, 2, 3, 4, 5]


@pytest.fixture
def other_data():
    return [6, 7]


def test_in_tree(tree_data):
    tree = build_tree(tree_data)

    assert all(in_tree(value, tree.root) for value in tree_data)


def test_not_in_tree(tree_data, other_data):
    tree = build_tree(tree_data)

    assert not any(in_tree(value, tree.root) for value in other_data)


def test_valid_proof(tree_data):
    tree = build_tree(tree_data)
    proofs = [create_proof(value, tree) for value in tree_data]

    assert all(
        validate_proof(value, proof, tree.root.hash)
        for value, proof in zip(tree_data, proofs)
    )


def test_invalid_proof(tree_data):
    tree = build_tree(tree_data)

    assert not validate_proof(tree_data[0], [], tree.root.hash)


def test_wrong_proof(tree_data):
    tree = build_tree(tree_data)
    proofs = [create_proof(value, tree) for value in tree_data]

    assert not validate_proof(tree_data[0], proofs[4], tree.root.hash)


def test_wrong_value(tree_data, other_data):
    tree = build_tree(tree_data)
    proofs = [create_proof(value, tree) for value in tree_data]

    assert not validate_proof(other_data[0], proofs[0], tree.root.hash)
