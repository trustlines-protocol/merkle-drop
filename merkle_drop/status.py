import pendulum
from deploy_tools.deploy import load_contracts_json
from eth_utils import to_checksum_address


def get_merkle_drop_status(web3, contract_address):

    compiled_contracts = load_contracts_json(__name__)

    merkle_drop_contract = web3.eth.contract(
        address=contract_address, abi=compiled_contracts["MerkleDrop"]["abi"]
    )

    token_contract = web3.eth.contract(
        address=merkle_drop_contract.functions.droppedToken().call(),
        abi=compiled_contracts["ERC20Interface"]["abi"],
    )

    return {
        "address": to_checksum_address(merkle_drop_contract.address),
        "root": merkle_drop_contract.functions.root().call(),
        "decay_start_time": merkle_drop_contract.functions.decayStartTime().call(),
        "decay_duration_in_seconds": merkle_drop_contract.functions.decayDurationInSeconds().call(),
        "initial_balance": merkle_drop_contract.functions.initialBalance().call(),
        "remaining_value": merkle_drop_contract.functions.remainingValue().call(),
        "spent_tokens": merkle_drop_contract.functions.spentTokens().call(),
        "token_address": to_checksum_address(token_contract.address),
        "token_name": token_contract.functions.name().call(),
        "token_symbol": token_contract.functions.symbol().call(),
        "token_decimals": token_contract.functions.decimals().call(),
        "token_balance": token_contract.functions.balanceOf(
            merkle_drop_contract.address
        ).call(),
        "decayed_remaining_value": merkle_drop_contract.functions.decayedEntitlementAtTime(
            merkle_drop_contract.functions.remainingValue().call(),
            pendulum.now().int_timestamp,
            True,
        ).call(),
    }
