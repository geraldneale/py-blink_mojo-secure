# py-blink_mojo-secure
Chialisp money privacy tool using non-interactive aggregated  <a href="https://www.iacr.org/archive/asiacrypt2001/22480516.pdf">Boneh-Lynn-Shacham (BLS) signatures</a> for security and a python3 driver for automatation and to make it less error prone.

* Runs on testnet10 by default. Use on mainnet ***AT YOUR OWN RISK!***
* Requires full node.
* There must be a small amount of mojos in the Faucet wallet before starting.
* Once you decide how much XCH needs privacy, there must be an equal or greater amount of XCH in both the Needs_Privacy and Decoy wallets to complete the transaction. For example, if you want 1 XCH to have privacy then there must be => 1 TXCH in both your Needs_Privacy and Decoy wallets before starting.
* Requires following prompts for various things including inputting Anonymous wallet address and Decoy wallet addresses to build the smart coins that will send value to those two target addresses in the spend bundle formed the end.
* Check out the accompanying video walkthrough for version 0.5 https://www.youtube.com/watch?v=9iGcu_PIIW8 .

Install
-------

Clone repository, go into it, make/activate a python virtualenv, and install requirements.

```
$ git clone https://github.com/geraldneale/py-blink_mojo-secure.git
$ cd py-blink_mojo-secure
$ python3 -m venv venv
$ . ./venv/bin/activate
$ pip3 install -r requirements.txt
```

Run
-------
Start the program.

```
$ python3 blink_mojo.py
```

Use
-------
Follow the prompts to deploy the coins from whatever wallet needs to be synced for the given step, as indicated.
![Screenshot from 2023-06-12 20-10-09](https://github.com/geraldneale/py-blink_mojo-secure/assets/53587595/fe4af5af-4e0e-4194-b1b2-8d67a5a90c78)



Final command
------
The final command will run automatically and spend all four of the coins you put on the blockchain at once in one block and in one spend bundle. If it does not run you can always copy and paste the following and attempt to run again manually. If that fails look to the log.txt file for guidance.
```
>> blink_mojo(faucet_coin,needs_privacy_coin,decoy_coin,decoy_value_coin)
```   
   
You should see
--------

`"status": "SUCCESS",
 "success": true`
 
 Mechanics
 ---------------
 The three items that make up a coinID are the ParentID, amount, and puzzle hash. ParentID is defined as the coinID whose chialisp outputted the CREATE_COIN op code to create this coin when spent.
 ![Screenshot from 2022-12-12 16-36-21](https://user-images.githubusercontent.com/53587595/207159821-cd5e2467-9a57-43d3-98f8-f02282c1d35e.png)

In blink_mojo the coinID from the faucet coin (in green) is passed to a newly formed coin in the Anonymous wallet as it's parentID and therefore keeps lineage to faucet as the final coin's "grand-parentID", despite it's value being much more than any of it's lineage. The value of the Needs_Privacy coin (in red) goes somewhere(possibly to the Anonymous wallet), but nobody can say for sure because another equal value coin is spent in a the same way as part of a paralell transaction in the same bundle and block (in brown). The lineage of the Needs_Privacy coin(in red) ends here in this block as does the Decoy coin(in brown). Their value goes somewhere in this block, but the exact location is indeterminate to all including the party running Blink Mojo, thereby increasing privacy.
![py-blink_mojo-secure](https://github.com/geraldneale/py-blink_mojo-secure/assets/53587595/b33c7751-0b19-4bb9-8e9e-edfae035368e)

 
Conclusion
---------
Chia blockchain offers major privacy opportunities over other decentralized blockchains, like Bitcoin, in three forms:
1)  Due to the attributes of BLS non-interactive aggregated signatures there is no certainty onchain of which coins went into which spend bundle in retrospect. There is just one aggregated signature per block. That signature canNOT be reverse engineered to any single spend bundle's aggregated signature. Each of the four blink_mojo coins is individually secured by its own randomly generated BLS key pair created on the fly by Blink Mojo, creating four disposable chia wallets, and aggregating the signatures from each of those at the end, securing the coins in the spend bundle from a subtraction attack. Each of the four public keys in the puzzle_reveals looks unassociated in retrospect to the auditor because they were created on the fly and will never used again. 
2)  In Chialisp, because it is a Lisp-derivative and a functional programming language, everything is evaluated in the instant of block formation. Therefore value is moved aribitrarily around a spend bundle, and within a block for that matter, to CREATE_COIN outputs in need of value. If there is >1 CREATE_COIN with deficit value and >! source of excess value in a spend bundle, or block because spend bundles are ephemeral and not auditable onchain, then it introduces doubt as to the source->destination realtionship of value transfer. This is what I call the "blink" in py-blink_mojo-secure. It's named after the mage spell in World of Warcraft by the same name which assists short range teleportation to avoid melee damage. 
3)  Perhaps the greatest attribute of this techniquie is usage of a fundamental to Chialisp which is how a puzzle hash represents arbitrary logic(CREATE_COIN etc). If we enlist a request to a faucet to send value to a newly created wallet and then send a portion of it's value to a custom created smart coin puzzle hash address then we effectively control some Chia blockchain logic anonymously, arbitrarily and can maintain a lineage that is not ours.

Using this technique one can consistenly direct equivalent value of the Needs_Privacy coin intentionally anywhere leaving only lineage to a public faucet onchain. Using a faucet is just an example of the technique's potential, cited for convenience. You could also do the same thing with pool rewards or other reliable sources potentially in the future. It is intended to leave the auditor, including the user of Blink Mojo, without certainty of the source->destination relationship of the value transfer. I encourage you to run this on Chia Testnet and challenge my assertion by submitting an issue here for public discourse. If it fails for any reason there is a log file which will help you diagnose the problem to create a successful spend by hand.

Please try it with _testnet only_. Use in mainnet only at your own risk.

Known issues and todos
---------
1) Todo: Make as many of the coin spends as possible in the final blink_mojo() transaction resemble a Chia wallet standard transaction. This will take time to learn how to do, but inspiration and reference can be found <a href = "https://github.com/richardkiss/chiaswap/blob/0c486088788266c43ab552cd2fcf5be76c919e31/chiaswap/main.py#L27">here</a>.
2) Todo: Expand the faucet coin functionality to chia Offers to complete the txs. In other words, either file a CHIP or hack Chia Offer spec to pay XCH to an aribitrary address. Right now it only pays to the wallet address that makes or takes the offer. This way the parent lineage of the offer maker/taker can be used and appended to the Needs_Privacy coin value without depending on public faucets which are historically spotty in their uptime. 
3) Issue: Incompatible with standalone wallet.

Also check out
------------
https://github.com/geraldneale/blink_mojo - the original proof of concept with a illustration of the basic concept and is meant to be easily repoducible and auditable.

Twitter @geraldneale

http://mojopuzzler.org - chialisp resources for the capable beginner.

Discord Mojo Puzzler - https://discord.gg/SMFHEE2Z

xch1hv4gj4vvdsyzn9hrhy9tn6hu6jwk82tyrs3t4r33468x642myjws8kh8xl
