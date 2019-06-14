import pytest
import eth_tester

from merkle_drop.merkle_tree import build_tree, Item, create_proof, validate_proof

# increase eth_tester's GAS_LIMIT
assert eth_tester.backends.pyevm.main.GENESIS_GAS_LIMIT < 8 * 10 ** 6
eth_tester.backends.pyevm.main.GENESIS_GAS_LIMIT = 8 * 10 ** 6


@pytest.fixture(scope="session")
def tree_data():
    return [
        Item(b"\xaa" * 20, 1_000_000),
        Item(b"\xbb" * 20, 2_000_000),
        Item(b"\xcc" * 20, 3_000_000),
        Item(b"\xdd" * 20, 4_000_000),
        Item(b"\xee" * 20, 5_000_000),
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
def eligible_address_0(tree_data):
    return tree_data[0].address


@pytest.fixture(scope="session")
def eligible_value_0(tree_data):
    return tree_data[0].value


@pytest.fixture(scope="session")
def proof_0(proofs_for_tree_data):
    return proofs_for_tree_data[0]


@pytest.fixture(scope="session")
def root_hash_for_tree_data(tree_data):
    tree = build_tree(tree_data)
    return tree.root.hash


@pytest.fixture(scope="session")
def premint_token_owner(accounts):
    return accounts[0]


@pytest.fixture(scope="session")
def premint_token_value():
    # The returned value should be equal to the dropped value: see values in `tree_data`
    return 15_000_000


@pytest.fixture(scope="session")
def dropped_token_contract(
    deploy_contract, root_hash_for_tree_data, premint_token_owner, premint_token_value
):
    # A token contract with premint token for the merkle drop.
    # The tokens are transferred to the MerkleDrop upon deployment of MerkleDrop.
    contract = deploy_contract(
        "DroppedToken",
        constructor_args=(
            "droppedToken",
            "DTN",
            18,
            premint_token_owner,
            premint_token_value,
        ),
    )

    return contract


@pytest.fixture(scope="session")
def decay_start_time():
    # 01/01/2100 at 00:00
    return 4_102_444_800


@pytest.fixture(scope="session")
def decay_duration():
    # two years
    return 3600 * 24 * 365 * 2


@pytest.fixture(scope="session")
def merkle_drop_contract(
    deploy_contract,
    root_hash_for_tree_data,
    dropped_token_contract,
    premint_token_owner,
    premint_token_value,
    decay_start_time,
    decay_duration,
):
    # The MerkleDrop contract owns enough token for airdropping
    contract = deploy_contract(
        "MerkleDrop",
        constructor_args=(
            dropped_token_contract.address,
            root_hash_for_tree_data,
            decay_start_time,
            decay_duration,
        ),
    )

    dropped_token_contract.functions.transfer(
        contract.address, premint_token_value
    ).transact({"from": premint_token_owner})
    assert (
        dropped_token_contract.functions.balanceOf(contract.address).call()
        == premint_token_value
    )

    return contract
