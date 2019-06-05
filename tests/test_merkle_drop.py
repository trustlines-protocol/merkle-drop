import pytest

import eth_tester.exceptions


def test_proof_entitlement(merkle_drop_contract, tree_data, proofs_for_tree_data):

    for i in range(len(proofs_for_tree_data)):
        address = tree_data[i].address
        value = tree_data[i].value
        proof = proofs_for_tree_data[i]
        assert merkle_drop_contract.functions.checkEntitlement(address, value, proof).call()


def test_incorrect_value_entitlement(merkle_drop_contract, tree_data, proofs_for_tree_data):
    address = tree_data[0].address
    incorrect_value = tree_data[0].value + 1234
    proof = proofs_for_tree_data[0]

    assert merkle_drop_contract.functions.checkEntitlement(address, incorrect_value, proof).call() is False


def test_incorrect_proof_entitlement(merkle_drop_contract, other_data, proofs_for_tree_data):
    address = other_data[0].address
    value = other_data[0].value
    incorrect_proof = proofs_for_tree_data[0]

    assert merkle_drop_contract.functions.checkEntitlement(address, value, incorrect_proof).call() is False
