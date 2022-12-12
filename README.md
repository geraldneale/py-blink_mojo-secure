# py-blink_mojo-secure
Chialisp money privacy tool using non-interactive aggregated  <a href="https://www.iacr.org/archive/asiacrypt2001/22480516.pdf">Boneh-Lynn-Shacham (BLS) signatures</a> for security. It uses a python3 driver for automatation and to make less error prone.

* Runs on testnet10 by default.
* Requires full node.
* Requires updating anonymous wallet and known wallet to your personal addresses. Can be edited into blink_mojo.py file or set at the prompt, as in: `anon_wallet = "txch<whateverwalletaddressyoudesire>"`


Install
-------

Clone repository, go into it, make and activate a virtualenv, and then install requirements.

```
$ git clone https://github.com/geraldneale/py-blink_mojo-secure.git
$ cd py-blink_mojo-secure
$ python3 -m venv venv
$ . ./venv/bin/activate
$ pip3 install -r requirements.txt
```

Edit the file blink_mojo.py
-------------
```
anon_wallet = "txch<whateverwalletaddressyoudesire>"
   
known_wallet = "txch<whateverotherwalletaddressyoudesire>"
   
value_amount = whatevervalueyoudesire
```
Run
-------
Start the program in interactive mode and optionally set the wallet variables to your own if you haven't done so already in the main file.

```
$ python3 -i blink_mojo.py
```

Use
-------
Follow the prompts to deploy and send the coins from whatever wallet is synced to the Chia blockchain.


Final command
------
The final command will run automatically and spend all four of the coins you put on the blockchain at once in one block and in one spend bundle. If it does not run you can always copy and paste the following to make it run again.
```
>> blink_mojo(faucet_coin,needs_privacy_coin,decoy_coin,decoy_value_coin)
```   
   
You should see
--------

`"status": "SUCCESS",
 "success": true`
 
 Mechanics
 ---------------
 The three items that make up a coinID are the amount, the puzzle hash and the parentID which is defined as the coin whose chialisp outputted the CREATE_COIN op code to create this coin when spent.
 ![Screenshot from 2022-12-12 16-36-21](https://user-images.githubusercontent.com/53587595/207159821-cd5e2467-9a57-43d3-98f8-f02282c1d35e.png)

In blink_mojo the coinID from the faucet coin (in green) is passed to a newly formed coin as it's parentID and therefore keeps reference to it's own parentID as the new coin's "grand-parentID", which of course points back to the faucet. The value of the coin needing privacy(in red) goes somewhere, but nobody can say for sure where because another equal value coin is spent in a similar way is right next to it on the block, the brown coin(not needing privacy). In any case, the lineage of the coin needing privacy ends here and it's value goes to an indeterminate place thereby increasing privacy.
 ![Screenshot from 2022-12-12 16-37-52](https://user-images.githubusercontent.com/53587595/207160076-fb19d161-54b7-4e66-a274-0aa2e62c5df5.png)

 
Conclusion
---------

Using this technique one can direct the equivalent value of the needs_privacy_coin intentionally to an anonymous wallet with only the lineage of a public faucet. It is intended to leave the auditor, including the user, without certainty if the mojos that were once in the needs_privacy_coin ended up in anon_wallet or known_wallet. I encourage you to run this on testnet and challenge my assertion by submitting an issue here for public discourse. If it fails for any reason there is a log file which will help you diagnose the problem and possibly recreate a successful spend by hand.

Chia-blockchain offers major privacy opportunities in three forms in this authour's opinion; which are:
1) In Chialisp everything is evaluated in the instant of block formation. Therefore value is moved aribitrarily around a spend bundle to CREATE_COIN outputs in need of value. If there is more than one CREATE_COIN with deficit value and more than one source of excess value in a spend bundle then it introduces doubt as to the source->destination of value transfer. This is what I call the "blink" in py-blink_mojo-secure. It's like the mage spell in World of Warcraft by the same name. 
2) Due to the attributes of BLS non-interactive aggregated signatures there is no certainty on the blockchain of which coins went into which spend bundle in retrospect. There is just one aggregated signature per block. That signature canNOT be reverse engineered to any single spend bundle's aggregated signature. Each coin is secured with its own BLS key pair created on the fly, much like creating four new chia wallets, and aggregating the signatures of each of those at the end securing the coins in the spend bundle from a subtraction attack, but each of the four public keys in the puzzle_reveals look unassociated in retrospect and never used again therefore secure.  
3) The puzzle hash for chia smart coins represents arbitrary logic(CREATE_COIN etc). If we request a faucet to send value to a smart coin puzzle hash address, instead of our own wallet, then we effectively can control some Chia blockchain logic anonymously, arbitrarily and from a public lineage.

Please try it with _testnet only_. Use in mainnet only at your own risk.

Known issues and todos
---------
1) Todo: Make as many of the coin spends as possible in the final blink_mojo() transaction resemble a Chia wallet standard transaction. This will take time to learn how to do, but inspiration and reference can be found <a href = "https://github.com/richardkiss/chiaswap/blob/0c486088788266c43ab552cd2fcf5be76c919e31/chiaswap/main.py#L27">here</a>.
2) Todo: The first guided step needs to be broken into two paths a. generating an address and using a faucet to do the spend or b. having blink_mojo do everything under the presumption that a faucet sent to a burner wallet fingerprint that will be used just this once. Right now it's only "b". 
2) Todo: Expand the faucet coin functionality to chia Offers to complete the txs. In other words, either file a CHIP or hack Chia Offer spec to pay XCH to an aribitrary address. Right now it only pays to the wallet address that makes or takes the offer. This way the parent lineage of the offer maker/taker can be commandeered and appeneded to the needs_privacy coin value without depending on public faucets which are historically spotty in their uptime. 
3) Issue: Incompatible with standalone wallet.

Also check out
------------
https://github.com/geraldneale/blink_mojo - the original proof of concept with a illustration of the basic concept and is meant to be easily repoducible and auditable.

Twitter @geraldneale

http://mojopuzzler.org - chialisp resources for the capable beginner.

Discord Mojo Puzzler - https://discord.gg/SMFHEE2Z

xch1hv4gj4vvdsyzn9hrhy9tn6hu6jwk82tyrs3t4r33468x642myjws8kh8xl
