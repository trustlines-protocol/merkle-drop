from merkle_drop.deploy import deploy_merkle_drop


def test_deploy(web3):
    zero_address = "0x0000000000000000000000000000000000000000"
    initial_balance = 123
    root = b"12"
    decay_start = 123
    decay_duration = 123
    constructor_args = (
        zero_address,
        initial_balance,
        root,
        decay_start,
        decay_duration,
    )
    merkle_drop = deploy_merkle_drop(web3=web3, constructor_args=constructor_args)

    assert merkle_drop.functions.initialBalance().call() == initial_balance
