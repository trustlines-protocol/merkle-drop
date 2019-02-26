import pytest
from click.testing import CliRunner

from merkle_drop.load_json import load_airdrop_dict
from merkle_drop.cli import main


airdrop_list = """{
                    "address1": 10,
                    "address2": 20
               }"""


@pytest.fixture()
def airdrop_list_file(tmp_path):
    folder = tmp_path / "subfolder"
    folder.mkdir()
    file_path = folder / "airdrop_list.json"
    file_path.write_text(airdrop_list)
    return file_path


@pytest.fixture()
def runner():
    return CliRunner()


def test_merkle_root_cli(runner, airdrop_list_file):

    result = runner.invoke(main, ["root", str(airdrop_list_file)])
    assert result.exit_code == 0


def test_read_json_file(airdrop_list_file):

    data = load_airdrop_dict(airdrop_list_file)
    assert data == {"address1": 10, "address2": 20}
