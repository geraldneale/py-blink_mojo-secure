# py-blink_mojo-secure
Chialisp money privacy tool using aggregated BLS signatures for security and Python3 for automation.

* Runs on testnet10 by default
* Need to update your own private key in blink_mojo.py file.
* Need to update your own public key in blink_mojo.py, faucet.clsp, needs_privacy.clsp, decoy.clsp, and decoy_value.clsp.

Basic steps are:
1. `python3 -i blink_mojo.py`.
2. `faucet_coin=deploy_smart_coin(FAUCET_CLSP,100)` and note coin_id if from other wallet(or from faucet).
3. `needs_privacy_coin=deploy_smart_coin(NEEDS_PRIVACY_CLSP,1000000000000)` and note coin_id if from other wallet.
4. As a final sequence:

   a. `decoy_coin=deploy_smart_coin(DECOY_CLSP,100)`
   
   b. `decoy_value_coin=deploy_smart_coin(DECOY_VALUE_CLSP,1000000000000)`
   
   c. `blink_mojo(faucet_coin,needs_privacy_coin,decoy_coin,decoy_value_coin)`.
   
   
Should see:
`"status": "SUCCESS",
 "success": true`
 
 Conclusion: Using this technique breaks the lineage of the needs_privacy_coin and directs its value somewhere intentionally, but without certainty to the auditor.
