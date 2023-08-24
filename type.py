from typing import TypedDict, List

LogDict = TypedDict(
    "LogDict",
    {
        "logpos": int,
        "address": str,
        "topics": List[str],
        "data": str,
    },
)

TxDict = TypedDict(
    "TxDict",
    {
        "txhash": str,
        "from": str,
        "to": str,
        "block_timestamp": int,
        "value": int,
        "gas": int,
        "input": str,
        "status": str,
        "logs": List[LogDict],
    },
)
