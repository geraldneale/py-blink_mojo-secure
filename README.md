# py-blink_mojo-secure
Chialisp money privacy tool using aggregated BLS signatures for security and Python3 for automation.

* Runs on testnet10 by default.
* Requires full node.
* Need to update your own private key, public key, anonymous wallet and known wallet in blink_mojo.py file.


Basic steps are:
1. `python3 -i blink_mojo.py`.
2. `faucet_coin=deploy_smart_coin(FAUCET_CLSP,100)` and note coin_id if from other wallet(or from faucet).
3. `needs_privacy_coin=deploy_smart_coin(NEEDS_PRIVACY_CLSP,1000)` and note coin_id if from other wallet.
4. As a final sequence:

   a. `decoy_coin=deploy_smart_coin(DECOY_CLSP,100)`
   
   b. `decoy_value_coin=deploy_smart_coin(DECOY_VALUE_CLSP,1000)`
   
   c. `blink_mojo(faucet_coin,needs_privacy_coin,decoy_coin,decoy_value_coin)`.
   
   
Should see:
`"status": "SUCCESS",
 "success": true`
 
 Conclusion: Using this technique breaks the lineage of the needs_privacy_coin and directs its value somewhere intentionally, but without certainty as to where from the perspective of the auditor. It is as simplistic a use of automated Python3 code to accomplish this task as possible. The complexity comes from the nature of the chia-blockchain which offers privacy opportunities in two forms in the opinion of the author; which are:
1) Puzzle hashes offer opportunity to inject logic at CREATE COIN so that the sending party, which becomes the parentid, cannot be held responsible for that logic and 
2) Everything is evaluated at the instant of block formation value via chialisp therefore value moves aribitrarily around a spend bundle offering the opportunity to insert doubt of source->destination relationship. That is what I call the "blink" in blink_mojo .
