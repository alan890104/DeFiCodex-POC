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

from events import EventLogsDecoder
from events import (
    UniswapV2Decoder,
    UniswapV3Decoder,
    AAVEV3Decoder,
    AAVEV2Decoder,
    CompoundV3Decoder,
)

from sqlalchemy.orm import sessionmaker
from model import Log, Transaction

import logging


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
db_url = f"postgresql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
engine = create_engine(db_url, echo=True)

if __name__ == "__main__":
    df = pd.read_csv("func_sign.csv")

    mc = Multicall("https://mainnet.infura.io/v3/84842078b09946638c03157f83405213")
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

    Session = sessionmaker(bind=engine)
    with Session() as session:
        txhash = "0x074abc8ba8aaa1374c00844540711bf62795ddcef891daf815863f24fc36e5dc"

        stmt_tx = select(Transaction).where(Transaction.txhash == txhash)
        result = session.scalars(stmt_tx).one()
        print(result.block_timestamp)
        print("from: ", get_addr_entry(result.from_address))
        print("to: ", get_addr_entry(result.to_address))
        print("value: ", get_value_entry(result.value))
        print("gas: ", get_gas_entry(result.gas))
        print("input: ", get_input_entry(result.input))
        print("status: ", get_status_entry(result.receipt_status))

        stmt_logs = select(Log).where(Log.txhash == txhash).order_by(Log.logpos)
        logs = session.scalars(stmt_logs).all()
        actions = []
        for log in logs:
            decoded = evt_decoder.decode(log)
            if decoded:
                actions.append(decoded)
        print("\n".join(actions))
