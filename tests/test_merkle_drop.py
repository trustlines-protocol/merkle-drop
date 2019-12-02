import math

import eth_tester.exceptions
import pytest
from eth_utils import to_checksum_address
from web3.exceptions import BadFunctionCallOutput


@pytest.fixture()
def merkle_drop_contract_already_withdrawn(
    merkle_drop_contract,
    dropped_token_contract,
    eligible_address_0,
    eligible_value_0,
    proof_0,
):
    merkle_drop_contract.functions.withdraw(eligible_value_0, proof_0).transact(
        {"from": eligible_address_0}
    )

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
        # Mining a block is usually considered here to fix unexpected behaviour with gas estimations
        # but that would make the chain time_travel past the exact decay_multiplier

    return time_travel


@pytest.fixture()
def time_travel_chain_past_decay_multiplier(chain, decay_start_time, decay_duration):
    def time_travel(decay_multiplier):
        time = int(decay_start_time + decay_duration * decay_multiplier)
        chain.time_travel(time)
        chain.mine_block()
        chain.mine_block()
        # we mine two blocks here, which should make sure we are past the decay_multiplier
        # both on the chain and as viewed by the broken gas estimation

    return time_travel


def decayed_value(value, decay_multiplier, round_up):
    decayed_value = value * (1 - decay_multiplier)
    if round_up:
        decayed_value = math.ceil(decayed_value)
    decayed_value = math.floor(decayed_value)
    return decayed_value


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
        merkle_drop_contract.functions.withdraw(value, proof).transact(
            {"from": address}
        )

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
        merkle_drop_contract_already_withdrawn.functions.withdraw(
            eligible_value_0, proof_0
        ).transact({"from": eligible_address_0})


def test_withdraw_wrong_proof(
    merkle_drop_contract_already_withdrawn, other_data, proof_0
):
    with pytest.raises(eth_tester.exceptions.TransactionFailed):
        merkle_drop_contract_already_withdrawn.functions.withdraw(
            other_data[0].value, proof_0
        ).transact({"from": other_data[0].address})


def test_withdraw_event(
    merkle_drop_contract, web3, eligible_address_0, eligible_value_0, proof_0
):

    latest_block_number = web3.eth.blockNumber

    merkle_drop_contract.functions.withdraw(eligible_value_0, proof_0).transact(
        {"from": eligible_address_0}
    )

    event = merkle_drop_contract.events.Withdraw.createFilter(
        fromBlock=latest_block_number
    ).get_all_entries()[0]["args"]

    assert event["recipient"] == to_checksum_address(eligible_address_0)
    assert event["value"] == eligible_value_0


@pytest.mark.parametrize(
    "decay_multiplier, round_up",
    [
        (0, True),
        (0.25, True),
        (0.5, True),
        (0.75, True),
        (1, True),
        (0, False),
        (0.25, False),
        (0.5, False),
        (0.75, False),
        (1, False),
    ],
)
def test_entitlement_with_decay(
    merkle_drop_contract, decay_start_time, decay_duration, decay_multiplier, round_up
):
    value = 99
    time = int(decay_start_time + decay_duration * decay_multiplier)

    expected_entitlement = decayed_value(value, decay_multiplier, round_up)

    assert (
        merkle_drop_contract.functions.decayedEntitlementAtTime(
            value, time, round_up
        ).call()
        == expected_entitlement
    )


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

    merkle_drop_contract.functions.withdraw(eligible_value_0, proof_0).transact(
        {"from": eligible_address_0}
    )

    assert dropped_token_contract.functions.balanceOf(
        eligible_address_0
    ).call() == decayed_value(eligible_value_0, decay_multiplier, False)


def test_entitlement_after_decay(
    merkle_drop_contract, decay_start_time, decay_duration
):
    value = 123456
    decay_multiplier = 2
    time = int(decay_start_time + decay_duration * decay_multiplier)
    assert (
        merkle_drop_contract.functions.decayedEntitlementAtTime(
            value, time, True
        ).call()
        == 0
    )


def test_withdraw_after_decay(
    merkle_drop_contract,
    time_travel_chain_past_decay_multiplier,
    eligible_address_0,
    eligible_value_0,
    proof_0,
):

    decay_multiplier = 2
    time_travel_chain_past_decay_multiplier(decay_multiplier)

    with pytest.raises(eth_tester.exceptions.TransactionFailed):
        merkle_drop_contract.functions.withdraw(eligible_value_0, proof_0).transact(
            {"from": eligible_address_0}
        )


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


def test_burn_tokens_after_decay_duration(
    merkle_drop_contract, dropped_token_contract, time_travel_chain_to_decay_multiplier
):
    decay_multiplier = 2
    time_travel_chain_to_decay_multiplier(decay_multiplier)

    merkle_drop_contract.functions.burnUnusableTokens().transact()
    balance = dropped_token_contract.functions.balanceOf(
        merkle_drop_contract.address
    ).call()

    assert balance == 0


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
    merkle_drop_contract.functions.withdraw(eligible_value_0, proof_0).transact(
        {"from": eligible_address_0}
    )

    expected_balance = decayed_value(eligible_value_0, decay_multiplier, False)

    # since we mined some blocks, the entitlement could have decayed by 1 in the meantime
    assert dropped_token_contract.functions.balanceOf(
        eligible_address_0
    ).call() == pytest.approx(expected_balance, abs=1)


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
    merkle_drop_contract.functions.withdraw(eligible_value_0, proof_0).transact(
        {"from": eligible_address_0}
    )

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
    # Test scenario with burn at two different times and withdraws
    # to see if every entitled user is able to withdraw and the final balance is 0

    decay_multiplier = 0.25
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.burnUnusableTokens().transact()

    decay_multiplier = 0.5
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.withdraw(eligible_value_0, proof_0).transact(
        {"from": eligible_address_0}
    )

    decay_multiplier = 0.75
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.burnUnusableTokens().transact()

    for i in range(1, len(proofs_for_tree_data)):
        address = tree_data[i].address
        value = tree_data[i].value
        proof = proofs_for_tree_data[i]

        merkle_drop_contract.functions.withdraw(value, proof).transact(
            {"from": address}
        )

    decay_multiplier = 1
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.burnUnusableTokens().transact()

    assert (
        dropped_token_contract.functions.balanceOf(merkle_drop_contract.address).call()
        == 0
    )


def test_burn_enough_token(
    merkle_drop_contract,
    dropped_token_contract,
    eligible_address_0,
    eligible_value_0,
    proof_0,
    time_travel_chain_to_decay_multiplier,
    premint_token_value,
):
    # test whether the value of token we burn is the maximum value we can burn.

    decay_multiplier = 0.5
    time_travel_chain_to_decay_multiplier(decay_multiplier)
    merkle_drop_contract.functions.withdraw(eligible_value_0, proof_0).transact(
        {"from": eligible_address_0}
    )

    merkle_drop_contract.functions.burnUnusableTokens().transact()

    assert (
        dropped_token_contract.functions.balanceOf(merkle_drop_contract.address).call()
        == (premint_token_value - eligible_value_0) * 0.5
    )


def test_self_destruct(
    merkle_drop_contract_already_withdrawn,
    eligible_address_0,
    time_travel_chain_past_decay_multiplier,
):
    time_travel_chain_past_decay_multiplier(1)
    assert (
        merkle_drop_contract_already_withdrawn.functions.withdrawn(
            eligible_address_0
        ).call()
        is True
    )

    merkle_drop_contract_already_withdrawn.functions.deleteContract().transact()

    with pytest.raises(BadFunctionCallOutput):
        # The contract is not there anymore, so the function call will fail
        merkle_drop_contract_already_withdrawn.functions.withdrawn(
            eligible_address_0
        ).call()


def test_self_destruct_too_soon(merkle_drop_contract):
    with pytest.raises(eth_tester.exceptions.TransactionFailed):
        merkle_drop_contract.functions.deleteContract().transact()


def test_yoichis_finding(
    merkle_drop_contract_small_values,
    time_travel_chain_to_decay_multiplier,
    dropped_token_contract,
    proofs_for_tree_data_small_values,
    tree_data_small_values,
):
    # Tests the finding by Yoichi during code review
    # Verifies that we round down on the amount of tokens to burn and to transfer to users
    # Uses exact expected number as provided during review

    merkle_drop = merkle_drop_contract_small_values
    time_travel_chain_to_decay_multiplier(0.5)

    merkle_drop.functions.burnUnusableTokens().transact()

    assert dropped_token_contract.functions.balanceOf(merkle_drop.address).call() == 50

    for i in range(1, len(proofs_for_tree_data_small_values)):
        address = tree_data_small_values[i].address
        value = tree_data_small_values[i].value
        proof = proofs_for_tree_data_small_values[i]
        merkle_drop.functions.withdraw(value, proof).transact({"from": address})
        assert dropped_token_contract.functions.balanceOf(address).call() == 16
