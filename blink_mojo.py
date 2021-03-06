import asyncio
from inspect import signature
from blspy import AugSchemeMPL, G2Element, G1Element, PrivateKey
import json
import time
import secrets
from cdv.util.load_clvm import load_clvm
from chia.util.byte_types import hexstr_to_bytes
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_spend import CoinSpend
from chia.types.spend_bundle import SpendBundle
from chia.util.bech32m import encode_puzzle_hash, decode_puzzle_hash
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.ints import uint16, uint64
from chia.wallet.transaction_record import TransactionRecord
import urllib.request
from decimal import Decimal

def print_json(dict):
    print(json.dumps(dict, sort_keys=True, indent=4))

FAUCET_CLSP, NEEDS_PRIVACY_CLSP, DECOY_CLSP, DECOY_VALUE_CLSP = "faucet.clsp", "needs_privacy.clsp", "decoy.clsp","decoy_value.clsp"
#define the following variables based on your needs
anon_wallet = "txch1qtx68z7xa05yvm9pxkyexkvewvnfvhgtcy54zzf9gln5yxkj9v4svna5rz" #for example
known_wallet = "txch1rdpgdacewwq0l8p4r9a4xzu3htccjqc4ynvgxnz7scn0569u7gfsn00mue" #for example
value_amount = 1000000000000
#switch ADD_DATA for environment
#ADD_DATA = bytes.fromhex("ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb") #genesis challenge(works for mainnet)
ADD_DATA = bytes.fromhex("ae83525ba8d1dd3f09b277de18ca3e43fc0af20d20c4b3e92ef2a48bd291ccb2")  #genesis challenge(works for testnet10)

config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
self_hostname = config["self_hostname"] # localhost
full_node_rpc_port = config["full_node"]["rpc_port"] # 8555
wallet_rpc_port = config["wallet"]["rpc_port"] # 9256


async def get_coin_async(coin_id: str):
    try:
        full_node_client = await FullNodeRpcClient.create(
                self_hostname, uint16(full_node_rpc_port), DEFAULT_ROOT_PATH, config
            )
        coin_record = await full_node_client.get_coin_record_by_name(bytes32.fromhex(coin_id))
        return coin_record.coin
    finally:
        full_node_client.close()
        await full_node_client.await_closed()

def get_coin(coin_id: str):
    return asyncio.run(get_coin_async(coin_id))

# Send from your default wallet on your machine
# Wallet has to be running, e.g., chia start wallet
async def send_money_async(amount, address, fee=10):
    wallet_id = "1"
    try:
        print(f"sending {amount} to {address}...")
        # create a wallet client
        wallet_client = await WalletRpcClient.create(
                self_hostname, uint16(wallet_rpc_port), DEFAULT_ROOT_PATH, config
            )
        # send standard transaction
        res = await wallet_client.send_transaction(wallet_id, amount, address, fee)
        tx_id = res.name
        print(f"waiting until transaction {tx_id} is confirmed...\nFor more info run from the terminal:")
        print(f"chia wallet get_transaction -tx {tx_id} -v")
        # wait until transaction is confirmed
        tx: TransactionRecord = await wallet_client.get_transaction(wallet_id, tx_id)
        while (not tx.confirmed):
            await asyncio.sleep(5)
            tx = await wallet_client.get_transaction(wallet_id, tx_id)
            print(".", end='', flush=True)
        # get coin infos including coin id of the addition with the same puzzle hash
        print(f"\ntx {tx_id} is confirmed.")
        puzzle_hash = decode_puzzle_hash(address)
        coin = next((c for c in tx.additions if c.puzzle_hash == puzzle_hash), None)
        print(f"coin {coin}")
        return coin
    finally:
        wallet_client.close()
        await wallet_client.await_closed()

def send_money(amount, address, fee):
    return asyncio.run(send_money_async(amount, address, fee))

#needs_privacy_coin=deploy_smart_coin(NEEDS_PRIVACY_CLSP,value_amount)
def deploy_smart_coin(clsp_file: str, amount: uint64, fee=10):
    s = time.perf_counter()
    # load coins (compiled and serialized, same content as clsp.hex)
    seed = secrets.token_bytes(32)
    print("Seed for {} coin: {}".format(clsp_file,seed))
    private_key: PrivateKey = AugSchemeMPL.key_gen(seed)
    #print("Private key for {}: {}".format(clsp_file, private_key))
    public_key: G1Element = private_key.get_g1()
    #print("Public key for {}: {}".format(clsp_file, public_key))
    msg = bytes.fromhex(secrets.token_hex(16))
    print("Message: {}".format(msg))
    if clsp_file in ["faucet.clsp", "decoy.clsp"]:
        mod = load_clvm(clsp_file, package_or_requirement=__name__).curry(public_key,msg,value_amount)
    else:    
        mod = load_clvm(clsp_file, package_or_requirement=__name__).curry(public_key,msg)
    print(mod)    
    # cdv clsp treehash
    treehash = mod.get_tree_hash()
    # cdv encode - txch->testnet10 or xch->mainnet
    address = encode_puzzle_hash(treehash, "xch")
    coin = send_money(amount, address, fee)
    elapsed = time.perf_counter() - s
    print(f"deploy {clsp_file} with {amount} mojos to {treehash} in {elapsed:0.2f} seconds.")
    print(f"coin_id: {coin.get_hash().hex()}")
    with open('log.txt', 'a') as log_file:
        prefix_name=clsp_file.split('.')
        log_file.write("{}_private_key: PrivateKey = AugSchemeMPL.key_gen({}".format(prefix_name[0],seed) + ")\n" + \
            "{}_public_key: G1Element = {}_private_key.get_g1()\n".format(prefix_name[0], prefix_name[0]) + \
            "{}_msg = {}\n".format(prefix_name[0], msg) + \
                "{}_coin = get_coin(\"{}\"), {}_private_key, {}_public_key, {}_msg\n\n".format(prefix_name[0], coin.get_hash().hex(), prefix_name[0], prefix_name[0],prefix_name[0])
                )
    log_file.close()
    
    return coin, private_key, public_key, msg

#this function is to obtain a target smart coin address to paste directly into a faucet
#an alternative is to have the faucet send to a disposable wallet address first and
#access it via your node and do the following from within blink_mojo:   faucet_coin=deploy_smart_coin(FAUCET_CLSP,1) #for example
def get_faucet_coin_address():
    s = time.perf_counter()
    #form specific key pair
    seed = secrets.token_bytes(32)
    print("Seed for {} coin: {}".format(FAUCET_CLSP,seed))
    private_key: PrivateKey = AugSchemeMPL.key_gen(seed)
    #print("Private key for {}: {}".format(clsp_file, private_key))
    public_key: G1Element = private_key.get_g1()
    #print("Public key for {}: {}".format(clsp_file, public_key))
    msg = bytes.fromhex(secrets.token_hex(16))
    print("Message: {}".format(msg))
    # load coins (compiled and serialized, same content as clsp.hex)
    mod = load_clvm(FAUCET_CLSP, package_or_requirement=__name__).curry(public_key,msg,value_amount)
    # cdv clsp treehash
    treehash = mod.get_tree_hash()
    # cdv encode - txch->testnet10 or xch->mainnet
    address = encode_puzzle_hash(treehash, "xch")
    print(f"Find a faucet and send a small amount of mojos to {address} ; for example 100 mojos")
    with open('log_faucet.txt', 'a') as log_file:
        prefix_name=FAUCET_CLSP.split('.')
        log_file.write("{}_private_key: PrivateKey = AugSchemeMPL.key_gen({}".format(prefix_name[0],seed) + ")\n" + \
            "{}_public_key: G1Element = {}_private_key.get_g1()\n".format(prefix_name[0], prefix_name[0]) + \
            "{}_msg = {}\n".format(prefix_name[0], msg) + \
                "{}_coin = get_coin(\"coinid from get_faucet_coin_info\"), {}_private_key, {}_public_key, {}_msg\n\n".format(prefix_name[0],prefix_name[0], prefix_name[0],prefix_name[0]) 
                )
    log_file.close()
    
    return address


#checks online for coinid needed to complete commands in log_faucet.txt
#then those commans to be copied and pasted into blink_mojo
#NOTE:the spacescan.io api only works for mainnet. 
#for testnet if you need to use this function, you need to send manually as follows: 
#chia wallet send -a 0.000000000010 -m 0.000000000010 -t ttxch1qtx68z7xa05yvm9pxkyexkvewvnfvhgtcy54zzf9gln5yxkj9v4svna5rz --override #for example
#cdv decode txch1qtx68z7xa05yvm9pxkyexkvewvnfvhgtcy54zzf9gln5yxkj9v4svna5rz #for example
#cdv rpc coinrecords --by puzhash 0xdeadbeef -nd to get the coinid and paste into log_faucet.txt #for example
def get_faucet_coin_info(address, faucet_coin_amount):
    root_url = "https://api2.spacescan.io"
    addr_url = f"{root_url}/1/xch/address/txns"
    while 1:
        print(f"checking for payments to {address}")
        resp = urllib.request.urlopen(f"{addr_url}/{address}", timeout=10)
        print(f"checking online here: {addr_url}/{address}")
        if resp.status == 200:
            coins = json.load(resp, parse_float=Decimal)["data"]["coins"][::-1]
            for coin in coins:
                amount = int(coin["amount"])
                if amount >= faucet_coin_amount:
                    with open('log_faucet.txt', 'a') as log_file:
                        prefix_name=FAUCET_CLSP.split('.')
                        log_file.write(
                            "{}_coin_info = {}\n\n".format(prefix_name[0],coin))
                        log_file.close()
                    #print("Coin Info: {}".format([coin]))    
                    return [coin]
        time.sleep(30)    

def solution_for_faucet(anon_wallet) -> Program:
    return Program.to([decode_puzzle_hash(anon_wallet)])

def solution_for_needs_privacy() -> Program:
    return Program.to([])

def solution_for_decoy(known_wallet) -> Program:
    return Program.to([decode_puzzle_hash(known_wallet)])

def solution_for_decoy_value() -> Program:
    return Program.to([])

async def push_tx_async(spend_bundle: SpendBundle):
    try:
        # create a full node client
        full_node_client = await FullNodeRpcClient.create(
                self_hostname, uint16(full_node_rpc_port), DEFAULT_ROOT_PATH, config
            )
        status = await full_node_client.push_tx(spend_bundle)
        return status
    finally:
        full_node_client.close()
        await full_node_client.await_closed()

def push_tx(spend_bundle: SpendBundle):
    return asyncio.run(push_tx_async(spend_bundle))

def blink_mojo(faucet_coin, needs_privacy_coin,decoy_coin, decoy_value_coin):
    # coin information, puzzle_reveal, and solution
    faucet_spend = CoinSpend(
        faucet_coin[0],
       load_clvm(FAUCET_CLSP, package_or_requirement=__name__).curry(faucet_coin[2],faucet_coin[3],value_amount),
        solution_for_faucet(anon_wallet)
    )
    needs_privacy_spend = CoinSpend(
        needs_privacy_coin[0],
        load_clvm(NEEDS_PRIVACY_CLSP, package_or_requirement=__name__).curry(needs_privacy_coin[2],needs_privacy_coin[3]),
        solution_for_needs_privacy()
    )
    decoy_spend = CoinSpend(
        decoy_coin[0],
       load_clvm(DECOY_CLSP, package_or_requirement=__name__).curry(decoy_coin[2],decoy_coin[3],value_amount),
        solution_for_decoy(known_wallet)
    )
    decoy_value_spend = CoinSpend(
        decoy_value_coin[0],
        load_clvm(DECOY_VALUE_CLSP, package_or_requirement=__name__).curry(decoy_value_coin[2],decoy_value_coin[3]),
        solution_for_decoy_value()
    )

    #signatures
    sig1 = AugSchemeMPL.sign(faucet_coin[1], faucet_coin[3] + bytes.fromhex(faucet_coin[0].get_hash().hex()) + ADD_DATA)
    sig2 = AugSchemeMPL.sign(needs_privacy_coin[1], needs_privacy_coin[3] + bytes.fromhex(needs_privacy_coin[0].get_hash().hex()) + ADD_DATA)
    sig3 = AugSchemeMPL.sign(decoy_coin[1], decoy_coin[3] + bytes.fromhex(decoy_coin[0].get_hash().hex()) + ADD_DATA)
    sig4 = AugSchemeMPL.sign(decoy_value_coin[1], decoy_value_coin[3] + bytes.fromhex(decoy_value_coin[0].get_hash().hex()) + ADD_DATA)
    signature: G2Element = AugSchemeMPL.aggregate([sig1, sig2, sig3, sig4])

    #spendBundle
    spend_bundle = SpendBundle(
            # coin spends
            [
                faucet_spend,
                needs_privacy_spend,
                decoy_spend,
                decoy_value_spend
            ],
            # aggregated_signature
            signature,
        )
    json_string=spend_bundle.to_json_dict()    
    print_json(json_string)
    #for reference only
    with open('spend_bundle.json', 'w') as spend_bundle_file:
        json.dump(json_string, spend_bundle_file, indent=4)
    spend_bundle_file.close()    
    status = push_tx(spend_bundle)
    print_json(status)
