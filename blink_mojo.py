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

def destination_puzzle_hash(address):
    if address.startswith(("xch","txch")):
        if address.startswith("txch"):
            puzzle_hash = decode_puzzle_hash(address[1:])
        else:
            puzzle_hash = decode_puzzle_hash(address)    
    return puzzle_hash

def print_json(dict):
    print(json.dumps(dict, sort_keys=True, indent=4))

FAUCET_CLSP, NEEDS_PRIVACY_CLSP, DECOY_CLSP, DECOY_VALUE_CLSP = "faucet.clsp", "needs_privacy.clsp", "decoy.clsp","decoy_value.clsp"
#define the following variables based on your needs
#anon_wallet = "xch1q3mdtrl999s0mdf0ud3sssfuatldq5hshlllj8l33uwjd4yj422q56d7h4" #for example
#known_wallet = "xch1vemls6m0c65shfmecadwq87tjs6x6jdmt2ktuucd87qaqh9pq2eqcfwqf9" #for example

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

#faucet_private_key: PrivateKey = AugSchemeMPL.key_gen(b'H\r\xc8_\xd9#\xed\xd3g\xa26W\x0bR\xfe\xeb\xb8\xe9%\x0es_elc\xa5\xea\xb1s\x8e\xf2\x91') #for example
#faucet_public_key: G1Element = faucet_private_key.get_g1() #for example
#faucet_coin=get_coin("56c68f1f840ff522fcd4ff7676d69725d7f39b35d15c01cc53a2cb0d012855d9"),faucet_private_key,faucet_public_key #for example
def get_coin(coin_id: str):
    return asyncio.run(get_coin_async(coin_id))

# Send from your default wallet on your machine
# Wallet has to be running, e.g., chia start wallet
async def send_money_async(amount, address, fee=100):
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

#send_money(10000,"txch1y9vvu4t3dd03w7gvvq5jn2ff7ckze5jc8uk3ek8fmahwrufw0jtq0wwgw7",100) #for example
#sometimes useful to run manually like this with higher fees to push 'INVALID_FEE_TOO_CLOSE_TO_ZERO' though in tandem
def send_money(amount, address, fee=2):
    return asyncio.run(send_money_async(amount, address, fee))

def deploy_smart_coin(clsp_file: str, amount: uint64, fee=100):
    s = time.perf_counter()
    # load coins (compiled and serialized, same content as clsp.hex)
    seed = secrets.token_bytes(32)
    print("Seed for {} coin: {}".format(clsp_file,seed))
    private_key: PrivateKey = AugSchemeMPL.key_gen(seed)
    #print("Private key for {}: {}".format(clsp_file, private_key))
    public_key: G1Element = private_key.get_g1()
    #print("Public key for {}: {}".format(clsp_file, public_key))
    mod = load_clvm(clsp_file, package_or_requirement=__name__).curry(public_key,msg)
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
                "{}_coin = get_coin(\"{}\"), {}_private_key, {}_public_key\n\n".format(prefix_name[0], coin.get_hash().hex(), prefix_name[0], prefix_name[0]))
    log_file.close()

    return coin, private_key, public_key

# opc '()'
def solution_for_faucet(anon_wallet) -> Program:
    return Program.to([destination_puzzle_hash(anon_wallet)])

def solution_for_needs_privacy() -> Program:
    return Program.to([])

def solution_for_decoy(known_wallet) -> Program:
    return Program.to([destination_puzzle_hash(known_wallet)])

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
       load_clvm(FAUCET_CLSP, package_or_requirement=__name__).curry(faucet_coin[2],msg),
        solution_for_faucet(anon_wallet)
    )
    needs_privacy_spend = CoinSpend(
        needs_privacy_coin[0],
        load_clvm(NEEDS_PRIVACY_CLSP, package_or_requirement=__name__).curry(needs_privacy_coin[2],msg),
        solution_for_needs_privacy()
    )
    decoy_spend = CoinSpend(
        decoy_coin[0],
       load_clvm(DECOY_CLSP, package_or_requirement=__name__).curry(decoy_coin[2],msg),
        solution_for_decoy(known_wallet)
    )
    decoy_value_spend = CoinSpend(
        decoy_value_coin[0],
        load_clvm(DECOY_VALUE_CLSP, package_or_requirement=__name__).curry(decoy_value_coin[2],msg),
        solution_for_decoy_value()
    )

    #signature
    DATA_TO_SIGN = msg #arbitrary message
    ADD_DATA= DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA #genesis challenge
    sig1 = AugSchemeMPL.sign(faucet_coin[1], DATA_TO_SIGN + bytes.fromhex(faucet_coin[0].get_hash().hex()) + ADD_DATA)
    sig2 = AugSchemeMPL.sign(needs_privacy_coin[1], DATA_TO_SIGN + bytes.fromhex(needs_privacy_coin[0].get_hash().hex()) + ADD_DATA)
    sig3 = AugSchemeMPL.sign(decoy_coin[1], DATA_TO_SIGN + bytes.fromhex(decoy_coin[0].get_hash().hex()) + ADD_DATA)
    sig4 = AugSchemeMPL.sign(decoy_value_coin[1], DATA_TO_SIGN + bytes.fromhex(decoy_value_coin[0].get_hash().hex()) + ADD_DATA)
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
    #write to normal looking spend_bundle.json file for reference
    with open('spend_bundle.json', 'w') as spend_bundle_file:
        json.dump(json_string, spend_bundle_file, indent=4)
    spend_bundle_file.close()    
    status = push_tx(spend_bundle)
    print_json(status)
