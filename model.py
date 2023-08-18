from sqlalchemy import (
    BIGINT,
    CHAR,
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    Numeric,
    UniqueConstraint,
    String,
    Text,
    text,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Log(Base):
    __tablename__ = "logs"
    __table_args__ = {"schema": "ethereum"}
    id = Column(BigInteger, primary_key=True)
    block_timestamp = Column(DateTime)
    _st = Column(Integer)
    _st_day = Column(Date)
    blknum = Column(BigInteger)
    txhash = Column(String(66))
    txpos = Column(BigInteger)
    logpos = Column(Integer)
    address = Column(String(42))
    n_topics = Column(Integer)
    topics = Column(Text)
    data = Column(Text)
    topics_0 = Column(Text)
    item_id = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class Transaction(Base):
    __tablename__ = "txs"
    __table_args__ = {"schema": "ethereum"}
    id = Column(Integer, primary_key=True)
    block_timestamp = Column(TIMESTAMP)
    _st = Column(Integer)
    _st_day = Column(Date)
    blknum = Column(BigInteger)
    txhash = Column(String(66), nullable=False)
    txpos = Column(BigInteger)
    nonce = Column(BigInteger)
    from_address = Column(String(42), nullable=False)
    to_address = Column(String(42))
    value = Column(Numeric)
    gas = Column(BigInteger)
    gas_price = Column(Numeric)
    input = Column(Text)
    max_fee_per_gas = Column(BigInteger)
    max_priority_fee_per_gas = Column(BigInteger)
    tx_type = Column(Integer)
    receipt_cumulative_gas_used = Column(BigInteger)
    receipt_gas_used = Column(BigInteger)
    receipt_contract_address = Column(Text)
    receipt_root = Column(Text)
    receipt_status = Column(Integer)
    receipt_effective_gas_price = Column(Numeric)
    receipt_log_count = Column(BigInteger)
    item_id = Column(Text)
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)


class Token(Base):
    __tablename__ = "tokens"
    __table_args__ = (UniqueConstraint("address"),)

    id = Column(BIGINT, primary_key=True, autoincrement=True)
    block_timestamp = Column(DateTime)
    _st = Column(Integer)
    _st_day = Column(Date)
    blknum = Column(BIGINT)
    txhash = Column(CHAR(66), nullable=False)
    txpos = Column(BIGINT)
    trace_address = Column(Text)
    address = Column(CHAR(42), nullable=False)
    symbol = Column(Text)
    name = Column(Text)
    decimals = Column(Integer)
    total_supply = Column(Numeric)
    is_erc20 = Column(Boolean)
    is_erc721 = Column(Boolean)
    is_erc1155 = Column(Boolean)
    source = Column(Text, default="contract")
    is_proxy = Column(Boolean)
    upstream = Column(Text)
    created_at = Column(DateTime, nullable=False, default="CURRENT_TIMESTAMP")
    updated_at = Column(DateTime, nullable=False, default="CURRENT_TIMESTAMP")
