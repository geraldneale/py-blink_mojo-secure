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
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.util.ints import uint16, uint64
from chia.wallet.transaction_record import TransactionRecord

def print_json(dict):
    print(json.dumps(dict, sort_keys=True, indent=4))

FAUCET_CLSP, NEEDS_PRIVACY_CLSP, DECOY_CLSP, DECOY_VALUE_CLSP = "faucet.clsp", "needs_privacy.clsp", "decoy.clsp","decoy_value.clsp"
known_wallet, anon_wallet = bytes.fromhex("0931bc0b32af0230d47e5d8d725ebe97d3a64da3b70d7b4750bb46b336daf745"), bytes.fromhex("459e69daa698a59f93e4cc0ac72add207539abd3047ef73dbcd917778cdd3948")

seed_faucet = secrets.token_bytes(32)
#print("Seed for faucet_coin: {}".format(seed_faucet))
secret_key_faucet: PrivateKey = AugSchemeMPL.key_gen(seed_faucet)
public_key_faucet: G1Element = secret_key_faucet.get_g1()

seed_needs_privacy = secrets.token_bytes(32)
#print("Seed for needs_privacy_coin: {}".format(seed_needs_privacy))
secret_key_needs_privacy: PrivateKey = AugSchemeMPL.key_gen(seed_needs_privacy)  
public_key_needs_privacy: G1Element = secret_key_needs_privacy.get_g1()

seed_decoy = secrets.token_bytes(32)
#print("Seed for decoy_coin: {}".format(seed_decoy))
secret_key_decoy : PrivateKey = AugSchemeMPL.key_gen(seed_decoy) 
public_key_decoy: G1Element = secret_key_decoy.get_g1()

seed_decoy_value = secrets.token_bytes(32)
#print("Seed for decoy_value_coin: {}".format(seed_decoy_value))
secret_key_decoy_value : PrivateKey = AugSchemeMPL.key_gen(seed_decoy_value) 
public_key_decoy_value: G1Element = secret_key_decoy_value.get_g1()

msg=bytes.fromhex("2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824")
# config/config.yaml
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

#faucet_coin=get_coin("97b5e4314819a2511deef9367ceecda813fcf30dc33f06fdbc1643ca04e6f67d") for example
#needs_privacy_coin=get_coin("6f450cae194f3cf7026537e3fa0d65e284984f934a1e5a23347fe4990890a52a") for example
#decoy_coin=get_coin("c4cee65fee52e01856793bc7c7022c92fe8bcf92864b0afb582fd3e63d4ff9a2") for example
#decoy_value_coin=get_coin("4e95629bd1690c5cb8559f024f8381723a8d3c170deb509da336ec91b92619db") for example
def get_coin(coin_id: str):
    return asyncio.run(get_coin_async(coin_id))

# Send from your default wallet on your machine
# Wallet has to be running, e.g., chia start wallet
async def send_money_async(amount, address, fee=2):
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
        print(f"waiting until transaction {tx_id} is confirmed...")
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

#send_money(10000,"txch1y9vvu4t3dd03w7gvvq5jn2ff7ckze5jc8uk3ek8fmahwrufw0jtq0wwgw7",100)
def send_money(amount, address, fee=2):
    return asyncio.run(send_money_async(amount, address, fee))

def deploy_smart_coin(clsp_file: str, amount: uint64, fee=2):
    s = time.perf_counter()
    # load coins (compiled and serialized, same content as clsp.hex)
    if clsp_file == "faucet.clsp":
        public_key = public_key_faucet 
    elif clsp_file == "needs_privacy.clsp":
        public_key = public_key_needs_privacy 
    elif clsp_file == "decoy.clsp":
        public_key = public_key_decoy
    elif clsp_file == "decoy_value.clsp":
        public_key = public_key_decoy_value
    mod = load_clvm(clsp_file, package_or_requirement=__name__).curry(public_key,msg)
    # cdv clsp treehash
    treehash = mod.get_tree_hash()
    # cdv encode - txch->testnet10 or xch->mainnet
    address = encode_puzzle_hash(treehash, "xch")
    coin = send_money(amount, address, fee)
    elapsed = time.perf_counter() - s
    print(f"deploy {clsp_file} with {amount} mojos to {treehash} in {elapsed:0.2f} seconds.")
    print(f"coin_id: {coin.get_hash().hex()}")

    return coin

# opc '()'
def solution_for_faucet(anon_wallet) -> Program:
    return Program.to([anon_wallet])

def solution_for_needs_privacy() -> Program:
    return Program.to([])

def solution_for_decoy(known_wallet) -> Program:
    return Program.to([known_wallet])

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

def blink_mojo(faucet_coin: Coin, needs_privacy_coin: Coin ,decoy_coin: Coin, decoy_value_coin: Coin):
    # coin information, puzzle_reveal, and solution
    faucet_spend = CoinSpend(
        faucet_coin,
       load_clvm(FAUCET_CLSP, package_or_requirement=__name__).curry(public_key_faucet,msg),
        solution_for_faucet(anon_wallet)
    )
    needs_privacy_spend = CoinSpend(
        needs_privacy_coin,
        load_clvm(NEEDS_PRIVACY_CLSP, package_or_requirement=__name__).curry(public_key_needs_privacy,msg),
        solution_for_needs_privacy()
    )
    decoy_spend = CoinSpend(
        decoy_coin,
       load_clvm(DECOY_CLSP, package_or_requirement=__name__).curry(public_key_decoy,msg),
        solution_for_decoy(known_wallet)
    )
    decoy_value_spend = CoinSpend(
        decoy_value_coin,
        load_clvm(DECOY_VALUE_CLSP, package_or_requirement=__name__).curry(public_key_decoy_value,msg),
        solution_for_decoy_value()
    )

    #signature
    # hex version of "hello", arbitrary message
    DATA_TO_SIGN = msg
    #genesis challenge
    ADD_DATA= DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
    sig1 = AugSchemeMPL.sign(secret_key_faucet, DATA_TO_SIGN + bytes.fromhex(faucet_coin.get_hash().hex()) + ADD_DATA)
    sig2 = AugSchemeMPL.sign(secret_key_needs_privacy, DATA_TO_SIGN + bytes.fromhex(needs_privacy_coin.get_hash().hex()) + ADD_DATA)
    sig3 = AugSchemeMPL.sign(secret_key_decoy, DATA_TO_SIGN + bytes.fromhex(decoy_coin.get_hash().hex()) + ADD_DATA)
    sig4 = AugSchemeMPL.sign(secret_key_decoy_value, DATA_TO_SIGN + bytes.fromhex(decoy_value_coin.get_hash().hex()) + ADD_DATA)
    signature: G2Element = AugSchemeMPL.aggregate([sig1, sig2, sig3, sig4])

    # SpendBundle
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
    #write to file for reference
    with open('spend_bundle.json', 'w') as outfile:
        json.dump(json_string, outfile)
    outfile.close()    
    status = push_tx(spend_bundle)
    print_json(status)
