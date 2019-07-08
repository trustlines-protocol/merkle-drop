# Trustlines Merkle-Drop

Example of usage to compute the merkle root from a json file containing certain addresses and balance:
```
merkle-drop root airdrop.csv
```

Example for `airdrop.csv`:
```
0xc2c543161A3B26DFb0a29a01c11351781Bff11F3,10
0xa1F7A26e4729de760D6074063F25054b4fA7bAb2,20
0x2147a30412206c6A39c7bf8aF10903020419024d,15
```

## Backend-Server

The best way to start the backend server is to use gunicorn as a WSGI-container:
```
pip install gunicorn
gunicorn -c config.py merkle_drop.server:app
```

Here is an example config file:
```
import merkle_drop.server

bind = "127.0.0.1:1234"
airdrop_filename = "airdrop.csv"
decay_start_time = 1559719024
decay_duration_in_seconds = 60 * 3600 * 24

workers = 8
max_requests = 1000


def on_starting(server):
    merkle_drop.server.init(
        airdrop_filename, decay_start_time, decay_duration_in_seconds
    )
```

## Requirements

- solidity compiler >= v0.5.8
