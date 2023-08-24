from os import getenv

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    desc,
    select,
    text,
)
from utils import (
    get_addr_entry,
    get_gas_entry,
    get_value_entry,
    get_input_entry,
    get_status_entry,
    format_timestamp,
)

import pandas as pd
from multicall import Multicall

from decoder import EventLogsDecoder
from decoder import (
    UniswapV2Decoder,
    UniswapV3Decoder,
    AAVEV3Decoder,
    AAVEV2Decoder,
    CompoundV3Decoder,
    BancorV3Decoder,
    CurveV2Decoder,
)

from sqlalchemy.orm import sessionmaker
from model import Log, Transaction

import logging
from web3 import Web3
from ens import ENS
import warnings
from provider import get_provider

warnings.filterwarnings("ignore")


logger = logging.getLogger("EventDecoder[Test]")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


provider_url = getenv("WEB3_PROVIDER_URL")
w3 = Web3(Web3.HTTPProvider(provider_url))
ns = ENS.fromWeb3(w3)

if __name__ == "__main__":
    df = pd.read_csv("func_sign.csv")
    mc = Multicall(provider_url)
    uniswap_v2 = UniswapV2Decoder(mc=mc, logger=logger)
    uniswap_v3 = UniswapV3Decoder(mc=mc, logger=logger)
    aave_v2 = AAVEV2Decoder(mc=mc, logger=logger)
    aave_v3 = AAVEV3Decoder(mc=mc, logger=logger)
    compound_v3 = CompoundV3Decoder(mc=mc, logger=logger)
    bancor_v3 = BancorV3Decoder(mc=mc, logger=logger)
    curve_v2 = CurveV2Decoder(mc=mc, logger=logger)

    evt_decoder = EventLogsDecoder(evt_df=df, verbose=False, logger=logger)
    evt_decoder.register_class(uniswap_v2)
    evt_decoder.register_class(uniswap_v3)
    evt_decoder.register_class(aave_v2)
    evt_decoder.register_class(aave_v3)
    evt_decoder.register_class(compound_v3)
    evt_decoder.register_class(bancor_v3)
    evt_decoder.register_class(curve_v2)

    p = get_provider("web3", w3=w3)

    while True:
        txhash = input("Please enter txhash: ")
        tx = p.get_tx_by_hash(txhash)
        print("=====================================")
        print("Transaction: ")
        print("Txhash: ", tx["txhash"])
        print("Timestamp: ", format_timestamp(tx["block_timestamp"]))
        print("From: ", ns.name(tx["from"]) or get_addr_entry(tx["from"]))
        print("To: ", get_addr_entry(tx["to"]))
        print("Gas: ", get_gas_entry(tx["gas"]))
        print("Value: ", get_value_entry(tx["value"]))
        print("Status: ", get_status_entry(tx["status"]))
        print("Input:\n\t", get_input_entry(tx["input"], evt_df=df))

        results = evt_decoder.decode_all(tx["logs"])
        for result in results:
            if result:
                print(result)
