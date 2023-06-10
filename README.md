# py-blink_mojo-secure
Chialisp money privacy tool using non-interactive aggregated  <a href="https://www.iacr.org/archive/asiacrypt2001/22480516.pdf">Boneh-Lynn-Shacham (BLS) signatures</a> for security. It uses a python3 driver for automatation and to make less error prone.

* Runs on testnet10 by default.
* Requires full node.
* Requires editing file blink_mojo.py for anonymous wallet and known wallet to your personal addresses. Can be alternatively set at the >> prompt when running the program, as in: `>>anon_wallet = "txch<whateverwalletaddressyoudesire>"`


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

```
Run
-------
Start the program in interactive mode and optionally set the wallet variables to your own if you haven't done so already in the main file.

```
$ python3 blink_mojo.py
```

Use
-------
Follow the prompts to deploy the coins from whatever wallet needs to be synced for the given step.

![image](https://user-images.githubusercontent.com/53587595/207199727-602c02f0-c350-4473-bc34-6353c1c2b7fe.png)


Final command
------
The final command will run automatically and spend all four of the coins you put on the blockchain at once in one block and in one spend bundle. If it does not run you can always copy and paste the following and attempt to run again manually.
```
>> blink_mojo(faucet_coin,needs_privacy_coin,decoy_coin,decoy_value_coin)
```   
   
You should see
--------

`"status": "SUCCESS",
 "success": true`
 
 Mechanics
 ---------------
 The three items that make up a coinID are the amount, the puzzle hash and the parentID. ParentID is defined as the coinID whose chialisp outputted the CREATE_COIN op code to create this coin when spent.
 ![Screenshot from 2022-12-12 16-36-21](https://user-images.githubusercontent.com/53587595/207159821-cd5e2467-9a57-43d3-98f8-f02282c1d35e.png)

In blink_mojo the coinID from the faucet coin (in green) is passed to a newly formed coin as it's parentID and therefore keeps reference to it's own parentID as the new coin's "grand-parentID", which of course points back to the faucet despite it's value being much less. The value of the coin needing privacy(in red) goes somewhere, but nobody can say for sure where because another equal value coin is spent in a similar way nearby on the same block (in brown). The lineage of the coin needing privacy(in red) ends here in this block as does the brown coin. Their value goes somewhere in this block, but the exact location is indeterminate thereby increasing privacy.
 ![Screenshot from 2022-12-12 16-37-52](https://user-images.githubusercontent.com/53587595/207160076-fb19d161-54b7-4e66-a274-0aa2e62c5df5.png)

 
Conclusion
---------

Using this technique one can direct the equivalent value of the needs_privacy_coin intentionally to an anonymous wallet with only the lineage of a public faucet. It is intended to leave the auditor, including the user, without certainty if the mojos that were once in the needs_privacy_coin ended up in anon_wallet or known_wallet. I encourage you to run this on testnet and challenge my assertion by submitting an issue here for public discourse. If it fails for any reason there is a log file which will help you diagnose the problem and possibly recreate a successful spend by hand.

Chia-blockchain offers major privacy opportunities over other decentralized blockchains like Bitcoin in three forms; which are:
1) In Chialisp, because it is a functional programming language, everything is evaluated in the instant of block formation. Therefore value is moved aribitrarily around a spend bundle to CREATE_COIN outputs in need of value. If there is more than one CREATE_COIN with deficit value and more than one source of excess value in a spend bundle then it introduces doubt as to the source->destination of value transfer. This is what I call the "blink" in py-blink_mojo-secure. It's like the mage spell in World of Warcraft by the same name. 
2) Due to the attributes of BLS non-interactive aggregated signatures there is no certainty on the blockchain of which coins went into which spend bundle in retrospect. There is just one aggregated signature per block. That signature canNOT be reverse engineered to any single spend bundle's aggregated signature. Each of the four blink_mojo coins is individually secured by its own randomly generated BLS key pair created on the fly by this program, much like creating a new chia wallet, and aggregating the signatures of each of those four coins at the end, securing the coins in the spend bundle from a subtraction attack. Each of the four public keys in the puzzle_reveals looks unassociated in retrospect because they were created on the fly and they will never used again.  
3) Perhaps the greatest attribute is how a puzzle hash in Chia represents arbitrary logic(CREATE_COIN etc). If we request a faucet to send value to a custom smart coin puzzle hash address, instead of our own wallet, then we effectively control some Chia blockchain logic. And we do so anonymously, arbitrarily and maintaining it's public lineage.

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
