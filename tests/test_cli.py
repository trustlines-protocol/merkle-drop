import pytest
from click.testing import CliRunner

from eth_utils import to_checksum_address, to_normalized_address, is_hex

from merkle_drop.load_csv import load_airdrop_file, validate_address_value_pairs
from merkle_drop.cli import main


A_ADDRESS = b"\xaa" * 20
B_ADDRESS = b"\xbb" * 20
C_ADDRESS = b"\xcc" * 20
D_ADDRESS = b"\xdd" * 20


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
        ((A_ADDRESS, "0"),),
        ((to_normalized_address(A_ADDRESS), "0"),),
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
    assert result.exit_code == 1
