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
 
 Conclusion: Using this technique directs needs_privacy_coin's value intentionally, but stops it's lineage and leaves the auditor without certainty as to where the value ended up. It is as simplistic a use of automated Python3 code to accomplish this task as possible. Complexity comes from the nature of Chia-blockchain which offers privacy opportunities in two forms, in the opinion of the author, which are:
1) Puzzle hashes offer opportunity to inject logic at CREATE COIN so that the sending party, which becomes the parentid, cannot be held responsible for that logic and 
2) Everything is evaluated at the instant of block formation by nature of chialisp being a functional programming language. Therefore value is moved aribitrarily around a spend bundle to coin creation outputs that need value. This introduces doubt of the source->destination relationship within a spend bundle. And importantly, the definition of which coins went into this spend bundle in mempool canNOT be reverse engineered from the blockchain after block formation(as far as I know). That is what I call the "blink" in blink_mojo.

Please try it and let me know what assumptions I might have wrong.

xch1hv4gj4vvdsyzn9hrhy9tn6hu6jwk82tyrs3t4r33468x642myjws8kh8xl

http://mojopuzzler.org
