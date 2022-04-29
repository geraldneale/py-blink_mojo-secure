# py-blink_mojo-secure
Chialisp money privacy tool using aggregated BLS signatures for security and Python3 for automation.

* Runs on testnet10 by default.
* Requires full node.
* Need to update your own private key, public key, anonymous wallet and known wallet in blink_mojo.py file.


Install
-------

Create and activate a virtualenv (first two lines), then install requirements.

```
$ python3 -m venv venv
$ . ./venv/bin/activate
$ pip3 install -r requirements.txt
```

Use
-------
```
$ python3 -i blink_mojo.py
$ faucet_coin=deploy_smart_coin(FAUCET_CLSP,100) NOTE: coin_id and BLS seed gets logged for reuse later if from another wallet.
$ needs_privacy_coin=deploy_smart_coin(NEEDS_PRIVACY_CLSP,1000)` NOTE: coin_id and BLS seed gets logged for reuse later if from another wallet.
$ decoy_coin=deploy_smart_coin(DECOY_CLSP,100)
$ decoy_value_coin=deploy_smart_coin(DECOY_VALUE_CLSP,1000)
```

As a final sequence
------
```
$ anon_wallet = "xch<whateverwalletaddressyoudesire>"
$ known_wallet = "xch<whateverotherwalletaddressyoudesire>"
$ blink_mojo(faucet_coin,needs_privacy_coin,decoy_coin,decoy_value_coin)
```   
   
You should see
--------

`"status": "SUCCESS",
 "success": true`
 
Conclusion
---------

Using this technique one can direct the equivalent value of the needs_privacy_coin intentionally to anon_wallet, but there is no lineage and it leaves any auditor, including the user of blink_mojo, without certainty if the mojos that were once in the needs_privacy_coin ended up in anon_wallet or known_wallet. 

Chia-blockchain offers major privacy opportunities in three forms; which are:
1) In Chialisp everything is evaluated at the instant of block formation by nature of it being a functional programming language. Therefore value is moved aribitrarily around a spend bundle to CREATE_COIN outputs in need of value. If there is more than one CREATE_COIN with deficit value in a spend bundle then it introduces doubt of the source->destination relationship of value. This is what I call the "blink" in blink_mojo.
2) Puzzle hashes for smart coins represent arbitrary logic(CREATE_COIN etc). If we request a faucet to send value to a smart coin, instead of our wallet, then we can control Chia blockchain logic anonymously.
4) Due to the magic of BLS aggregated signatures there is no certainty on the blockchain of which coins went into which spend bundle in retrospect. There is just one aggregated signature per block. That signature canNOT be reverse engineered to any single spend bundle's aggregated signature with reliability(NOTE: this is as far as I know. please feel free to disagree, but tell me why). The same feature is used within the blink_mojo spend bundle securing each coin with its own BLS key pair and aggregating the signatures at the end securing the coins in the spend bundle from a subtraction attack, but each of the four public keys in the puzzle_reveals look unassociated in retrospect.  

Please try it with _in testnet only_. If used in mainnet it is at your own risk.

xch1hv4gj4vvdsyzn9hrhy9tn6hu6jwk82tyrs3t4r33468x642myjws8kh8xl

http://mojopuzzler.org
