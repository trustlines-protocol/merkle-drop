import pytest

import eth_tester.exceptions
from eth_utils import to_checksum_address


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


@pytest.fixture()
def time_travel_chain_to_decay_multiplier(chain, decay_start_time, decay_duration):
    def time_travel(decay_multiplier):
        time = int(decay_start_time + decay_duration * decay_multiplier)
        chain.time_travel(time)
        chain.mine_block()

    return time_travel


def test_proof_entitlement(merkle_drop_contract, tree_data, proofs_for_tree_data):

    for i in range(len(proofs_for_tree_data)):
        address = tree_data[i].address
        value = tree_data[i].value
        proof = proofs_for_tree_data[i]
        assert merkle_drop_contract.functions.verifyEntitled(
            address, value, proof
        ).call()


def test_incorrect_value_entitlement(
    merkle_drop_contract, tree_data, proofs_for_tree_data
):
    address = tree_data[0].address
    incorrect_value = tree_data[0].value + 1234
    proof = proofs_for_tree_data[0]

    assert (
        merkle_drop_contract.functions.verifyEntitled(
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
        merkle_drop_contract.functions.verifyEntitled(
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


def test_withdraw_event(
    merkle_drop_contract, web3, eligible_address_0, eligible_value_0, proof_0
):

    latest_block_number = web3.eth.blockNumber

    merkle_drop_contract.functions.withdrawFor(
        eligible_address_0, eligible_value_0, proof_0
    ).transact()

    event = merkle_drop_contract.events.Withdraw.createFilter(
        fromBlock=latest_block_number
    ).get_all_entries()[0]["args"]

    assert event["recipient"] == to_checksum_address(eligible_address_0)
    assert event["value"] == eligible_value_0


@pytest.mark.parametrize("decay_multiplier", [0, 0.25, 0.5, 0.75, 1])
def test_entitlement_with_decay(
    merkle_drop_contract, decay_start_time, decay_duration, decay_multiplier
):
    value = 123456
    time = int(decay_start_time + decay_duration * decay_multiplier)
    assert merkle_drop_contract.functions.decayedEntitlementAtTime(
        value, time
    ).call() == value * (1 - decay_multiplier)


@pytest.mark.parametrize("decay_multiplier", [0, 0.25, 0.5, 0.75])
def test_withdraw_with_decay(
    merkle_drop_contract,
    dropped_token_contract,
    time_travel_chain_to_decay_multiplier,
    decay_multiplier,
    eligible_address_0,
    eligible_value_0,
    proof_0,
):
    time_travel_chain_to_decay_multiplier(decay_multiplier)

    merkle_drop_contract.functions.withdrawFor(
        eligible_address_0, eligible_value_0, proof_0
    ).transact()

    assert dropped_token_contract.functions.balanceOf(
        eligible_address_0
    ).call() == eligible_value_0 * (1 - decay_multiplier)


def test_entitlement_after_decay(
    merkle_drop_contract, decay_start_time, decay_duration
):
    value = 123456
    decay_multiplier = 2
    time = int(decay_start_time + decay_duration * decay_multiplier)
    assert (
        merkle_drop_contract.functions.decayedEntitlementAtTime(value, time).call() == 0
    )


def test_withdraw_after_decay(
    merkle_drop_contract,
    time_travel_chain_to_decay_multiplier,
    eligible_address_0,
    eligible_value_0,
    proof_0,
):

    decay_multiplier = 2
    time_travel_chain_to_decay_multiplier(decay_multiplier)

    with pytest.raises(eth_tester.exceptions.TransactionFailed):
        merkle_drop_contract.functions.withdrawFor(
            eligible_address_0, eligible_value_0, proof_0
        ).transact()


@pytest.mark.parametrize("decay_multiplier", [0, 0.25, 0.5, 0.75, 1])
def test_burn_unusable_tokens(
    merkle_drop_contract,
    dropped_token_contract,
    time_travel_chain_to_decay_multiplier,
    decay_multiplier,
):
    time_travel_chain_to_decay_multiplier(decay_multiplier)

    balance_before = dropped_token_contract.functions.balanceOf(
        merkle_drop_contract.address
    ).call()
    merkle_drop_contract.functions.burnUnusableTokens().transact()
    balance_after = dropped_token_contract.functions.balanceOf(
        merkle_drop_contract.address
    ).call()

    assert balance_after == (1 - decay_multiplier) * balance_before


@pytest.mark.parametrize("decay_multiplier", [0, 0.25, 0.5, 0.75])
def test_withdraw_after_burn(
    merkle_drop_contract,
    dropped_token_contract,
    time_travel_chain_to_decay_multiplier,
    decay_multiplier,
    eligible_address_0,
    eligible_value_0,
    proof_0,
):
    time_travel_chain_to_decay_multiplier(decay_multiplier)

    merkle_drop_contract.functions.burnUnusableTokens().transact()
    merkle_drop_contract.functions.withdrawFor(
        eligible_address_0, eligible_value_0, proof_0
    ).transact()

    assert dropped_token_contract.functions.balanceOf(
        eligible_address_0
    ).call() == eligible_value_0 * (1 - decay_multiplier)


def test_balance_null_after_withdraw_and_burn(
    merkle_drop_contract,
    dropped_token_contract,
    eligible_address_0,
    eligible_value_0,
    proof_0,
    time_travel_chain_to_decay_multiplier,
):
    # Test scenario with burn at two different times and a withdraw
    # to see if the final balance is indeed 0 and no errors are raised.

    decay_multiplier = 0.25
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.burnUnusableTokens().transact()

    decay_multiplier = 0.5
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.withdrawFor(
        eligible_address_0, eligible_value_0, proof_0
    ).transact()

    decay_multiplier = 0.75
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.burnUnusableTokens().transact()

    decay_multiplier = 1
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.burnUnusableTokens().transact()

    assert (
        dropped_token_contract.functions.balanceOf(merkle_drop_contract.address).call()
        == 0
    )


def test_everyone_can_withdraw_after_burns(
    merkle_drop_contract,
    dropped_token_contract,
    eligible_address_0,
    eligible_value_0,
    proof_0,
    tree_data,
    proofs_for_tree_data,
    time_travel_chain_to_decay_multiplier,
):
    # Test scenario with burn at two different times and a withdraw
    # to see if every entitled user is able to withdraw and the final balance is 0

    decay_multiplier = 0.25
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.burnUnusableTokens().transact()

    decay_multiplier = 0.5
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.withdrawFor(
        eligible_address_0, eligible_value_0, proof_0
    ).transact()

    decay_multiplier = 0.75
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.burnUnusableTokens().transact()

    for i in range(1, len(proofs_for_tree_data)):
        address = tree_data[i].address
        value = tree_data[i].value
        proof = proofs_for_tree_data[i]

        merkle_drop_contract.functions.withdrawFor(address, value, proof).transact()

    decay_multiplier = 1
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.burnUnusableTokens().transact()

    assert (
        dropped_token_contract.functions.balanceOf(merkle_drop_contract.address).call()
        == 0
    )
