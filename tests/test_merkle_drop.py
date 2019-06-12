import pytest

import eth_tester.exceptions


@pytest.fixture()
def merkle_drop_contract_already_withdrawn(
    merkle_drop_contract,
    dropped_token_contract,
    eligible_address_0,
    eligible_value_0,
    proof_0,
):
    merkle_drop_contract.functions.withdrawFor(
        eligible_address_0, eligible_value_0, proof_0
    ).transact()

    assert (
        dropped_token_contract.functions.balanceOf(eligible_address_0).call()
        == eligible_value_0
    )

    return merkle_drop_contract


def test_proof_entitlement(merkle_drop_contract, tree_data, proofs_for_tree_data):

    for i in range(len(proofs_for_tree_data)):
        address = tree_data[i].address
        value = tree_data[i].value
        proof = proofs_for_tree_data[i]
        assert merkle_drop_contract.functions.checkEntitlement(
            address, value, proof
        ).call()


def test_incorrect_value_entitlement(
    merkle_drop_contract, tree_data, proofs_for_tree_data
):
    address = tree_data[0].address
    incorrect_value = tree_data[0].value + 1234
    proof = proofs_for_tree_data[0]

    assert (
        merkle_drop_contract.functions.checkEntitlement(
            address, incorrect_value, proof
        ).call()
        is False
    )


def test_incorrect_proof_entitlement(
    merkle_drop_contract, other_data, proofs_for_tree_data
):
    address = other_data[0].address
    value = other_data[0].value
    incorrect_proof = proofs_for_tree_data[0]

    assert (
        merkle_drop_contract.functions.checkEntitlement(
            address, value, incorrect_proof
        ).call()
        is False
    )


def test_withdraw(
    merkle_drop_contract, tree_data, proofs_for_tree_data, dropped_token_contract
):
    for i in range(len(proofs_for_tree_data)):
        merkle_drop_balance = dropped_token_contract.functions.balanceOf(
            merkle_drop_contract.address
        ).call()

        address = tree_data[i].address
        value = tree_data[i].value
        proof = proofs_for_tree_data[i]
        merkle_drop_contract.functions.withdrawFor(address, value, proof).transact()

        assert dropped_token_contract.functions.balanceOf(address).call() == value
        assert (
            dropped_token_contract.functions.balanceOf(
                merkle_drop_contract.address
            ).call()
            == merkle_drop_balance - value
        )


def test_withdraw_already_withdrawn(
    merkle_drop_contract_already_withdrawn,
    eligible_address_0,
    eligible_value_0,
    proof_0,
):
    with pytest.raises(eth_tester.exceptions.TransactionFailed):
        merkle_drop_contract_already_withdrawn.functions.withdrawFor(
            eligible_address_0, eligible_value_0, proof_0
        ).transact()


def test_withdraw_wrong_proof(
    merkle_drop_contract_already_withdrawn, other_data, proof_0
):
    with pytest.raises(eth_tester.exceptions.TransactionFailed):
        merkle_drop_contract_already_withdrawn.functions.withdrawFor(
            other_data[0].address, other_data[0].value, proof_0
        ).transact()
