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
anon_wallet = "txch1znjytxf23nz7lcrqdg52djuct8rhfjg36e9ph2vm2s2pfc9z38yqez6rcr" #for example
known_wallet = "txch150trmj9g08555k3qaptn0sl5dseq0recwmvgn73cdtch2dc3t0ksjuespy" #for example
value_amount = 1000000000111
default_fee = 1000      #mojos
#switch for environment mainnet or testnest10
#ADD_DATA = bytes.fromhex("ccd5bb71183532bff220ba46c268991a3ff07eb358e8255a65c30a2dce0e5fbb") #genesis challenge(works for mainnet)
ADD_DATA = bytes.fromhex("ae83525ba8d1dd3f09b277de18ca3e43fc0af20d20c4b3e92ef2a48bd291ccb2")  #genesis challenge(works for testnet10)

config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
self_hostname = config["self_hostname"] # localhost
full_node_rpc_port = config["full_node"]["rpc_port"] # 8555
wallet_rpc_port = config["wallet"]["rpc_port"] # 9256

#these functions are here in case something goes wrong and you need to troublshoot using entries in log files
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

# Send from synced wallet on your machine e.g., chia start wallet
async def send_money_async(amount, address, fee=default_fee):
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
def deploy_smart_coin(clsp_file: str, amount: uint64, fee=default_fee):
    s = time.perf_counter()
    seed = secrets.token_bytes(32)
    print("Seed for {} coin: {}".format(clsp_file,seed))
    private_key: PrivateKey = AugSchemeMPL.key_gen(seed)
    #print("Private key for {}: {}".format(clsp_file, private_key))
    public_key: G1Element = private_key.get_g1()
    #print("Public key for {}: {}".format(clsp_file, public_key))
    msg = bytes.fromhex(secrets.token_hex(16))
    print("Message: {}".format(msg))
    if clsp_file == "faucet.clsp":
        mod = load_clvm(clsp_file, package_or_requirement=__name__).curry(public_key,msg,value_amount,decode_puzzle_hash(anon_wallet))
    elif clsp_file == "decoy.clsp":
        mod = load_clvm(clsp_file, package_or_requirement=__name__).curry(public_key,msg,value_amount,decode_puzzle_hash(known_wallet))
    else:    
        mod = load_clvm(clsp_file, package_or_requirement=__name__).curry(public_key,msg)
    print(mod)    
    # cdv clsp treehash
    treehash = mod.get_tree_hash()
    # cdv encode - txch->testnet10 or xch->mainnet
    if ADD_DATA == bytes.fromhex("ae83525ba8d1dd3f09b277de18ca3e43fc0af20d20c4b3e92ef2a48bd291ccb2"):
        chain_prefix = "txch"
    else:
        chain_prefix = "xch"   
    address = encode_puzzle_hash(treehash, chain_prefix)
    coin = send_money(amount, address, fee)
    elapsed = time.perf_counter() - s
    print(f"deploy {clsp_file} with {amount} mojos to {treehash} in {elapsed:0.2f} seconds.")
    print(f"coin_id: {coin.name().hex()}")
    with open('log.txt', 'a') as log_file:
        prefix_name=clsp_file.split('.')
        log_file.write("{}_private_key: PrivateKey = AugSchemeMPL.key_gen({}".format(prefix_name[0],seed) + ")\n" + \
            "{}_public_key: G1Element = {}_private_key.get_g1()\n".format(prefix_name[0], prefix_name[0]) + \
            "{}_msg = {}\n".format(prefix_name[0], msg) + \
                "{}_coin = get_coin(\"{}\"), {}_private_key, {}_public_key, {}_msg\n\n".format(prefix_name[0], coin.name().hex(), prefix_name[0], prefix_name[0],prefix_name[0])
                )
    log_file.close()
    
    return coin, private_key, public_key, msg

def solution_for_faucet() -> Program:
    return Program.to([])

def solution_for_needs_privacy() -> Program:
    return Program.to([])

def solution_for_decoy() -> Program:
    return Program.to([])

def solution_for_decoy_value() -> Program:
    return Program.to([])

async def push_tx_async(spend_bundle: SpendBundle):
    try:
        # create a full node client
        full_node_client = await FullNodeRpcClient.create(
                self_hostname, uint16(full_node_rpc_port), DEFAULT_ROOT_PATH, config
            )
        print("Fees: {}".format(spend_bundle.fees()))    
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
       load_clvm(FAUCET_CLSP, package_or_requirement=__name__).curry(faucet_coin[2],faucet_coin[3],value_amount,decode_puzzle_hash(anon_wallet)),
        solution_for_faucet()
    )
    needs_privacy_spend = CoinSpend(
        needs_privacy_coin[0],
        load_clvm(NEEDS_PRIVACY_CLSP, package_or_requirement=__name__).curry(needs_privacy_coin[2],needs_privacy_coin[3]),
        solution_for_needs_privacy()
    )
    decoy_spend = CoinSpend(
        decoy_coin[0],
       load_clvm(DECOY_CLSP, package_or_requirement=__name__).curry(decoy_coin[2],decoy_coin[3],value_amount,decode_puzzle_hash(known_wallet)),
        solution_for_decoy()
    )
    decoy_value_spend = CoinSpend(
        decoy_value_coin[0],
        load_clvm(DECOY_VALUE_CLSP, package_or_requirement=__name__).curry(decoy_value_coin[2],decoy_value_coin[3]),
        solution_for_decoy_value()
    )

    #signatures
    sig1 = AugSchemeMPL.sign(faucet_coin[1], faucet_coin[3] + bytes.fromhex(faucet_coin[0].name().hex()) + ADD_DATA)
    sig2 = AugSchemeMPL.sign(needs_privacy_coin[1], needs_privacy_coin[3] + bytes.fromhex(needs_privacy_coin[0].name().hex()) + ADD_DATA)
    sig3 = AugSchemeMPL.sign(decoy_coin[1], decoy_coin[3] + bytes.fromhex(decoy_coin[0].name().hex()) + ADD_DATA)
    sig4 = AugSchemeMPL.sign(decoy_value_coin[1], decoy_value_coin[3] + bytes.fromhex(decoy_value_coin[0].name().hex()) + ADD_DATA)
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


if __name__=='__main__':

    def ready_verification(question):

        while "the answer is invalid":
            reply = str(input(question+' (y/n): ')).lower().strip()
            if reply[:1] == 'y':
                return True
    default_relay_coin_value = 10000 #this becomes excess value in the final spend and therefore fees
    wallet_ready_faucet = ready_verification('Faucet Coin wallet synced and ready? Typically this is low value burner wallet.')
    if wallet_ready_faucet:
        faucet_coin=deploy_smart_coin(FAUCET_CLSP,default_relay_coin_value,default_fee)
        wallet_privacy_ready = ready_verification('Needs Privacy wallet synced and ready?')
        if wallet_privacy_ready:    
            needs_privacy_coin=deploy_smart_coin(NEEDS_PRIVACY_CLSP,value_amount)
            wallet_decoy_ready = ready_verification('Decoy wallet synced and ready? Typically this is a well funded wallet.')
            if wallet_decoy_ready:     
                decoy_coin=deploy_smart_coin(DECOY_CLSP,default_relay_coin_value,default_fee)
                decoy_value_coin=deploy_smart_coin(DECOY_VALUE_CLSP,value_amount)           

    blink_mojo(faucet_coin,needs_privacy_coin,decoy_coin,decoy_value_coin)
