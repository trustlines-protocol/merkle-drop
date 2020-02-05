# Trustlines Merkle-Drop

## Installation via PyPI

Please run `pip install merkle-drop` in fresh virtualenv using at
least python 3.6.

## Installation from git checkout

Please make sure you have the following requirements installed:

- solidity compiler >= v0.5.8
- python >= 3.6

Activate a fresh virtualenv and run `make install`. This will install
the `merkle-drop` program. Please run `merkle-drop --help` to get an
overview of available command line options. This document covers only
a subset of the available options.


## Compute the merkle root

The `root` subcommand computes the merkle root from a CSV file
containing addresses and balances.

```shell
$ merkle-drop root airdrop.csv
0x5a7973598b5c9040bb842e4ff16c4685b4fd4bd1ac62645b9b844a9df35592d6
```

Example for `airdrop.csv`:
```CSV
0xc2c543161A3B26DFb0a29a01c11351781Bff11F3,10000000000000000000
0xa1F7A26e4729de760D6074063F25054b4fA7bAb2,20000000000000000000
0x2147a30412206c6A39c7bf8aF10903020419024d,15000000000000000001
0xc8EC4CCa92AaA39B5dD24493670c63Dfb74D36e0,1500000000000000000
0x45eEC844d18f1dbeFD6Ac784552BC86f303BA07B,1800000000000000000
```

Please be aware that you need to specify balances with the full
decimal count (i.e. in wei)


## Running the backend server

The best way to start the backend server is to use gunicorn as a WSGI-container:

```shell
gunicorn -c config.py merkle_drop.server:app
```

The following config is suitable for the Trustlines Foundations
currently active [Merkle Drop Token
Claim](https://trustlines.foundation/merkle-drop.html).

You can find the `airdrop.csv` file for that in the [merkle-drop-data
repository](https://github.com/trustlines-protocol/merkle-drop-data).

```python
import merkle_drop.server

bind = "0.0.0.0:8080"
airdrop_filename = "airdrop.csv"
decay_start_time = 1577833140
decay_duration_in_seconds = 63158400  # 2 years

workers = 4
max_requests = 500


def on_starting(server):
    merkle_drop.server.init_gunicorn_logging()
    merkle_drop.server.init_cors(origins="*")
    merkle_drop.server.init(
        airdrop_filename, decay_start_time, decay_duration_in_seconds
    )
```

### Generating a proof via GET request

With the server running, you can generate a proof by calling curl or http:
```
$ http http://localhost:8080/entitlement/0x00000000007F6202Ba718DF41ec639b32Dd7fBCF
HTTP/1.1 200 OK
Access-Control-Allow-Origin: *
Connection: close
Content-Length: 1471
Content-Type: application/json
Date: Thu, 30 Jan 2020 10:43:55 GMT
Server: gunicorn/19.9.0

{
    "address": "0x00000000007F6202Ba718DF41ec639b32Dd7fBCF",
    "currentTokenBalance": "204385112839531052032",
    "originalTokenBalance": "212976887600000000000",
    "proof": [
        "0x975abbe47f8637e8f048bf838f59d081162e5b549518a8f465385be9bf16102d",
        "0x28fac2c585927d7d7c1f43bdbc37aa8c561f1ad7e8b52466acb2f2ac7b11e4a5",
        "0x64c80aeb687d4d1a28600cfec22d0dbd4f3c3455cf0e4d6c2aaf8c1916769bc4",
        "0x4b848b4f810b2129913be0ae2e374abeecab72243cb98f361cb1c68d96f6cbe8",
        "0x100b182a927b2b4ddfb0ce959008d20dc71296b2610a125c82ca85acc286dad7",
        "0x28716fd1643fb3e7388d2494f36cf802292588d2cbd6d3170f99d80eeeb25b5e",
        "0xd762cf132b42da6a15c11ab7dd47cae5e3cb5dc4c260737535e88920b6f02209",
        "0x16070ef5fad1b3a0a1d8a05c5b023007aa7c2fa644ef858f2551f07c3816b8b1",
        "0xd0ac1aee8a660c0f4bd003f9afddb956819f75eb72064d1246f5ad4d9488b663",
        "0xa7022577eb35dbce83c3cf7d74a86394300211096fd3f55561f89a22108a1924",
        "0x317e02325e8f0bd9dec6afc4449fc4e0cb8bfbedfaa3dae02cc50640196252b3",
        "0x5c308d95607cce2091a2eca114d0b3964c7381e574ddbc24589ad812a9974735",
        "0x0f58b54296b8ab1b1c582308bb30fa0d2167b5aab94c30d95f785e4ab4d38b3b",
        "0xa171f84c30a2060c7430c5207d8cf8c24f6e5430e4f4c80db441c9d662aae426",
        "0x296cd18ee97193654eb82078de8d1d37d98ccb6cad261da7ae2593161bfa7455",
        "0x95bf1328bcae3de81d2ebe03069f447937d681d1caa25f788aec576b8b6203af",
        "0x2ea199528b5586a57124356972d412fe6e1f99356c716f2432204d6ad0d17f6a",
        "0x3567daef60454362d49a375347426f5e0b0cc5d914f57338a25a709cbcbb010d",
        "0x0fd54647afad0616b0d051eb8408349f525a1f8981809f963bd52ac0eb73d849"
    ]
}
```

## Generating a proof via the command line

The `proof` subcommand can be used to generate a proof from the command line:

```
$ merkle-drop proof  0x00000000007F6202Ba718DF41ec639b32Dd7fBCF /path/to/merkle-drop-data/airdrop.csv
0x975abbe47f8637e8f048bf838f59d081162e5b549518a8f465385be9bf16102d 0x28fac2c585927d7d7c1f43bdbc37aa8c561f1ad7e8b52466acb2f2ac7b11e4a5 0x64c80aeb687d4d1a28600cfec22d0dbd4f3c3455cf0e4d6c2aaf8c1916769bc4 0x4b848b4f810b2129913be0ae2e374abeecab72243cb98f361cb1c68d96f6cbe8 0x100b182a927b2b4ddfb0ce959008d20dc71296b2610a125c82ca85acc286dad7 0x28716fd1643fb3e7388d2494f36cf802292588d2cbd6d3170f99d80eeeb25b5e 0xd762cf132b42da6a15c11ab7dd47cae5e3cb5dc4c260737535e88920b6f02209 0x16070ef5fad1b3a0a1d8a05c5b023007aa7c2fa644ef858f2551f07c3816b8b1 0xd0ac1aee8a660c0f4bd003f9afddb956819f75eb72064d1246f5ad4d9488b663 0xa7022577eb35dbce83c3cf7d74a86394300211096fd3f55561f89a22108a1924 0x317e02325e8f0bd9dec6afc4449fc4e0cb8bfbedfaa3dae02cc50640196252b3 0x5c308d95607cce2091a2eca114d0b3964c7381e574ddbc24589ad812a9974735 0x0f58b54296b8ab1b1c582308bb30fa0d2167b5aab94c30d95f785e4ab4d38b3b 0xa171f84c30a2060c7430c5207d8cf8c24f6e5430e4f4c80db441c9d662aae426 0x296cd18ee97193654eb82078de8d1d37d98ccb6cad261da7ae2593161bfa7455 0x95bf1328bcae3de81d2ebe03069f447937d681d1caa25f788aec576b8b6203af 0x2ea199528b5586a57124356972d412fe6e1f99356c716f2432204d6ad0d17f6a 0x3567daef60454362d49a375347426f5e0b0cc5d914f57338a25a709cbcbb010d 0x0fd54647afad0616b0d051eb8408349f525a1f8981809f963bd52ac0eb73d849
```
