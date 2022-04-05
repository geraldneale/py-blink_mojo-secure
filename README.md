# py-blink_mojo-secure
Chialisp money privacy tool using aggregated BLS signatures for security and Python3 for automation.

* Runs on testnet10 by default
* Need to update your own private key in blink_mojo.py file.
* Need to update your own public key in blink_mojo.py, faucet.clsp, needs_privacy.clsp, decoy.clsp, and decoy_value.clsp.

Basic steps are:
1. Create faucet_coin and note coin_id.
2. Create needs_privacy_coin and note coin_id.
3. As a final sequence create decoy_coin, decoy_value_coin, reference the coin_ids in steps 1 & 2, and blink_mojo(). Done.
