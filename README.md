# py-blink_mojo-secure
Chialisp money privacy tool using aggregated BLS signatures for security and Python3 for automation.

* Runs on testnet10 by default.
* Requires full node.
* Need to update your own private key, public key, anonymous wallet and known wallet in blink_mojo.py file.


Basic steps for *NIX are:
1. `python3 -m venv venv`
2. `. ./venv/bin/activate`
3. `pip3 install -r requirements.txt`
4. `python3 -i blink_mojo.py`.
5. `faucet_coin=deploy_smart_coin(FAUCET_CLSP,100)` NOTE coin_id and private key if from another wallet(or from faucet).
6. `needs_privacy_coin=deploy_smart_coin(NEEDS_PRIVACY_CLSP,1000)` NOTE coin_id and private key if from another wallet.
7. As a final sequence:

   a. `decoy_coin=deploy_smart_coin(DECOY_CLSP,100)`
   
   b. `decoy_value_coin=deploy_smart_coin(DECOY_VALUE_CLSP,1000)`
   
   c. `blink_mojo(faucet_coin,needs_privacy_coin,decoy_coin,decoy_value_coin)`.
   
   
Should see:
`"status": "SUCCESS",
 "success": true`
 
 Conclusion: Using this technique stops the lineage of the needs_privacy_coin directing its value intentionally, but without certainty as to where from the perspective of the auditor. It is as simplistic a use of automated Python3 code to accomplish this task as possible. Any complexity comes from the nature of the chia-blockchain which offers privacy opportunities in two forms in the opinion of the author; which are:
1) Puzzle hashes offer opportunity to inject logic at CREATE COIN so that the sending party, which becomes the parentid, cannot be held responsible for that logic and 
2) Everything is evaluated at the instant of block formation via chialisp feautre as a functional programming language, therefore value is moved aribitrarily around a spend bundle to spends that need it offering the opportunity to insert doubt of the value source->destination relationship. And importantly, the exact nature of a spend bundle canNOT be reverse engineered form the blockchain. That is what I call the "blink" in blink_mojo .
