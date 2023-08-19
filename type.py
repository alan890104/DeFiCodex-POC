from typing import TypedDict, List

LogDict = TypedDict(
    "LogDict",
    {
        "logpos": int,
        "address": str,
        "topics": str,
        "data": str,
    },
)

TxDict = TypedDict(
    "TxDict",
    {
        "txhash": str,
        "from": str,
        "to": str,
        "value": int,
        "gas": int,
        "input": str,
        "status": str,
        "logs": List[LogDict],
    },
)
