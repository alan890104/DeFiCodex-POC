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
)

from sqlalchemy.orm import sessionmaker
from model import Log, Transaction

import logging
from web3 import Web3

from provider import get_provider

w3 = Web3()

logger = logging.getLogger("EventDecoder[Test]")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


db_username = getenv("DB_USERNAME")
db_password = getenv("DB_PASSWORD")
db_host = getenv("DB_HOST")
db_port = getenv("DB_PORT")
db_name = getenv("DB_NAME")
provider_url = getenv("WEB3_PROVIDER_URL")
db_url = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(db_url, echo=True)

if __name__ == "__main__":
    df = pd.read_csv("func_sign.csv")
    mc = Multicall(provider_url)
    uniswap_v2 = UniswapV2Decoder(mc=mc, logger=logger)
    uniswap_v3 = UniswapV3Decoder(mc=mc, logger=logger)
    aave_v2 = AAVEV2Decoder(mc=mc, logger=logger)
    aave_v3 = AAVEV3Decoder(mc=mc, logger=logger)
    compound_v3 = CompoundV3Decoder(mc=mc, logger=logger)

    evt_decoder = EventLogsDecoder(evt_df=df, verbose=True, logger=logger)
    evt_decoder.register_class(uniswap_v2)
    evt_decoder.register_class(uniswap_v3)
    evt_decoder.register_class(aave_v2)
    evt_decoder.register_class(aave_v3)
    evt_decoder.register_class(compound_v3)

    p = get_provider("web3", w3=Web3(Web3.HTTPProvider(provider_url)))

    while True:
        txhash = input("Please enter txhash: ")
        tx = p.get_tx(txhash)
        results = evt_decoder.decode_all(tx["logs"])
        for result in results:
            if result:
                print(result)
