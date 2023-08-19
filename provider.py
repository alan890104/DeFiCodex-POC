from abc import ABC, abstractmethod
from type import TxDict, LogDict
from typing import Literal, List
from os import getenv
from sqlalchemy.engine import Engine, create_engine
from sqlalchemy.orm import sessionmaker, Session
from model import Transaction, Log
from web3 import Web3
from sqlalchemy import select
from web3.types import TxReceipt, LogReceipt


class BaseProvider(ABC):
    def __init__(self) -> None:
        pass

    @abstractmethod
    def get_tx(self, txhash: str) -> TxDict:
        raise NotImplementedError


class SQLProvider:
    def __init__(self, dialect: Literal["postgresql"] = "postgresql") -> None:
        db_username = getenv("DB_USERNAME")
        db_password = getenv("DB_PASSWORD")
        db_host = getenv("DB_HOST")
        db_port = getenv("DB_PORT")
        db_name = getenv("DB_NAME")
        db_url = (
            f"{dialect}://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
        self.engine: Engine = create_engine(db_url, echo=True)

    def _make_logs(self, logs: list[Log]) -> list[LogDict]:
        return [
            {
                "logpos": log.logpos,
                "address": log.address,
                "topics": log.topics,
                "data": log.data,
            }
            for log in logs
        ]

    def get_tx(self, txhash: str) -> TxDict:
        SessFactory = sessionmaker(bind=self.engine)
        with SessFactory() as sess:
            stmt_tx = select(Transaction).where(Transaction.txhash == txhash)
            result = sess.scalars(stmt_tx).one()

            stmt_logs = select(Log).where(Log.txhash == txhash).order_by(Log.logpos)
            logs = sess.scalars(stmt_logs).all()

            return {
                "txhash": result.txhash,
                "from": result.from_address,
                "to": result.to_address,
                "value": result.value,
                "gas": result.gas,
                "input": result.input,
                "status": result.receipt_status,
                "logs": self._make_logs(logs),
            }


class Web3Provider:
    def __init__(self, w3: Web3) -> None:
        self.w3 = w3

    def _get_logs(self, logs: List[LogReceipt]) -> List[LogDict]:
        return [
            {
                "logpos": log["logIndex"],
                "address": log["address"],
                "topics": [topic.hex() for topic in log["topics"] if topic],
                "data": log["data"],
            }
            for log in logs
        ]

    def get_tx(self, txhash: str) -> TxDict:
        tx = self.w3.eth.get_transaction(txhash)
        rtn: TxReceipt = self.w3.eth.getTransactionReceipt(txhash)
        return {
            "txhash": rtn["transactionHash"].hex(),
            "from": rtn["from"],
            "to": rtn["to"],
            "value": tx["value"],
            "gas": rtn["gasUsed"],
            "input": tx["input"] if tx["input"] else "0x",
            "status": rtn["status"],
            "logs": self._get_logs(rtn["logs"]),
        }


def get_provider(p: Literal["web3", "sql"], **kwargs) -> BaseProvider:
    if p == "web3":
        return Web3Provider(**kwargs)
    elif p == "sql":
        return SQLProvider(**kwargs)
    else:
        raise ValueError(f"Invalid provider: {p}")
