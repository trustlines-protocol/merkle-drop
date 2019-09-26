import pendulum
import pytest
from click.testing import CliRunner
from deploy_tools.cli import connect_to_json_rpc
from deploy_tools.deploy import deploy_compiled_contract, load_contracts_json
from eth_utils import is_hex, to_checksum_address
from web3.contract import Contract

from merkle_drop.cli import main
from merkle_drop.load_csv import load_airdrop_file, validate_address_value_pairs

A_ADDRESS = b"\xaa" * 20
B_ADDRESS = b"\xbb" * 20
C_ADDRESS = b"\xcc" * 20
D_ADDRESS = b"\xdd" * 20

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


AIRDROP_DATA = {A_ADDRESS: 10, B_ADDRESS: 20, D_ADDRESS: 30}


def is_encoded_hash32(value: str) -> bool:
    return is_hex(value) and len(value) == 2 + 2 * 32


@pytest.fixture()
def airdrop_list_file(tmp_path):
    folder = tmp_path / "subfolder"
    folder.mkdir()
    file_path = folder / "airdrop_list.csv"
    file_path.write_text(
        "\n".join(
            (
                ",".join((to_checksum_address(address), str(value)))
                for address, value in AIRDROP_DATA.items()
            )
        )
    )
    return file_path


@pytest.fixture()
def runner():
    return CliRunner()


def test_merkle_root_cli(runner, airdrop_list_file):

    result = runner.invoke(main, ["root", str(airdrop_list_file)])
    assert result.exit_code == 0
    result_without_newline = result.output.rstrip()
    assert is_encoded_hash32(result_without_newline)


def test_read_csv_file(airdrop_list_file):

    data = load_airdrop_file(airdrop_list_file)
    assert data == AIRDROP_DATA


@pytest.mark.parametrize(
    "address_value_pairs",
    [
        (),
        ((to_checksum_address(A_ADDRESS), "0"),),
        ((to_checksum_address(A_ADDRESS), "0"), (to_checksum_address(B_ADDRESS), "0")),
        ((to_checksum_address(A_ADDRESS), str(2 ** 256 - 1)),),
    ],
)
def test_valid_airdrop_file_validation(address_value_pairs):
    validate_address_value_pairs(address_value_pairs)


@pytest.mark.parametrize(
    "address_value_pairs",
    [
        ((),),
        ((to_checksum_address(A_ADDRESS),)),
        ((to_checksum_address(A_ADDRESS), "0", "a third entry"),),
        ((to_checksum_address(A_ADDRESS), "0"), (to_checksum_address(A_ADDRESS), "0")),
        ((to_checksum_address(A_ADDRESS), "0xaa"),),
        ((to_checksum_address(A_ADDRESS), "-3"),),
        ((to_checksum_address(A_ADDRESS), "1.2"),),
        (("0", to_checksum_address(A_ADDRESS)),),
    ],
)
def test_invalid_airdrop_file_validation(address_value_pairs):
    with pytest.raises(ValueError):
        validate_address_value_pairs(address_value_pairs)


def test_merkle_balance_cli(runner, airdrop_list_file):

    result = runner.invoke(
        main, ["balance", to_checksum_address(A_ADDRESS), str(airdrop_list_file)]
    )
    assert result.exit_code == 0
    assert int(result.output) == AIRDROP_DATA[A_ADDRESS]


def test_merkle_not_existing_balance_cli(runner, airdrop_list_file):

    result = runner.invoke(
        main, ["balance", to_checksum_address(C_ADDRESS), str(airdrop_list_file)]
    )
    assert result.exit_code == 0
    assert int(result.output) == 0


def test_merkle_proof_cli(runner, airdrop_list_file):

    result = runner.invoke(
        main, ["proof", to_checksum_address(A_ADDRESS), str(airdrop_list_file)]
    )
    assert result.exit_code == 0
    proof = result.output.split()
    assert len(proof) == 2
    for field in proof:
        assert is_encoded_hash32(field)


def test_not_existing_merkle_proof_cli(runner, airdrop_list_file):

    result = runner.invoke(
        main, ["proof", to_checksum_address(C_ADDRESS), str(airdrop_list_file)]
    )
    assert result.exit_code == 2


def test_deploy_cli(runner, airdrop_list_file):
    result = runner.invoke(
        main,
        args=f"deploy --jsonrpc test --token-address {ZERO_ADDRESS} "
        f"--airdrop-file {airdrop_list_file} --decay-start-time 123456789",
    )

    print(result.output)
    assert result.exit_code == 0


def test_deploy_cli_with_date(runner, airdrop_list_file):
    result = runner.invoke(
        main,
        args=f"deploy --jsonrpc test --token-address {ZERO_ADDRESS} "
        f"--airdrop-file {airdrop_list_file} --decay-start-date 2020-12-12",
    )

    print(result.output)
    assert result.exit_code == 0


def test_status_cli(runner, root_hash_for_tree_data, premint_token_value):

    # Deploy Token & Contract. This could be refactored into fixtures, but it's only used for this specific case.
    web3 = connect_to_json_rpc("test")
    compiled_contracts = load_contracts_json("merkle_drop")

    token_contract: Contract = deploy_compiled_contract(
        abi=compiled_contracts["DroppedToken"]["abi"],
        bytecode=compiled_contracts["DroppedToken"]["bytecode"],
        constructor_args=(
            "Test Token",
            "TT",
            18,
            web3.eth.accounts[0],
            premint_token_value,
        ),
        web3=web3,
    )

    merkle_drop_contract: Contract = deploy_compiled_contract(
        abi=compiled_contracts["MerkleDrop"]["abi"],
        bytecode=compiled_contracts["MerkleDrop"]["bytecode"],
        constructor_args=(
            token_contract.address,
            premint_token_value,
            root_hash_for_tree_data,
            pendulum.now().int_timestamp + 10,
            60 * 60 * 24 * 4,
        ),
        web3=web3,
    )

    # Get Status - This should result in the insufficient funds warning
    result = runner.invoke(
        main,
        args=f"status --jsonrpc test --merkle-drop-address {merkle_drop_contract.address}",
    )

    assert result.exit_code == 0

    # Check for funding warning
    assert "Token Balance is lower than Decayed Remaining Value." in result.output

    # Fund contract
    token_contract.functions.storeAddressOfMerkleDrop(
        merkle_drop_contract.address
    ).transact()
    token_contract.functions.transfer(
        merkle_drop_contract.address, premint_token_value
    ).transact()
    assert (
        token_contract.functions.balanceOf(merkle_drop_contract.address).call()
        == premint_token_value
    )

    # Get Status - Again, this time without warning
    result = runner.invoke(
        main,
        args=f"status --jsonrpc test --merkle-drop-address {merkle_drop_contract.address}",
    )

    print(result.output)
    assert result.exit_code == 0

    assert "Token Balance is lower than Decayed Remaining Value." not in result.output
    assert "Test Token (TT)" in result.output
    assert token_contract.address in result.output
    assert merkle_drop_contract.address in result.output
    assert "in 4 days" in result.output
