from typing import Dict, List, Tuple, Union
from itertools import chain
from eth_abi import decode


def eth_decode_log(event_abi: Dict, topics: List[str], data: str) -> Tuple[str, Dict]:
    # Ensure ABI is a valid event
    if "name" not in event_abi or event_abi.get("type") != "event":
        return "{}", {}

    # Separate indexed and non-indexed inputs
    indexed_inputs, non_indexed_inputs = partition_inputs(event_abi.get("inputs", []))

    func_signature = create_function_signature(
        event_abi["name"], indexed_inputs + non_indexed_inputs
    )

    indexed_values = decode_values_from_topics(indexed_inputs, topics)
    non_indexed_values = decode_values_from_data(non_indexed_inputs, data)

    # Merge indexed and non-indexed values
    parameters = merge_parameters(indexed_values, non_indexed_values)

    # Convert byte data to hex
    convert_bytes_to_hex(parameters)

    return func_signature, parameters


def partition_inputs(inputs: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    indexed, non_indexed = [], []
    for input in inputs:
        if input.get("indexed"):
            indexed.append(input)
        else:
            non_indexed.append(input)
    return indexed, non_indexed


def create_function_signature(name: str, inputs: List[Dict]) -> str:
    return "{}({})".format(
        name,
        ", ".join([f"{input['type']} {input.get('name', '')}" for input in inputs]),
    )


def decode_values_from_topics(indexed_inputs: List[Dict], topics: List[str]) -> Dict:
    return {
        input["name"]: decode([input["type"]], bytes.fromhex(topic[2:]))[0]
        for input, topic in zip(indexed_inputs, topics[1:])
    }


def decode_values_from_data(non_indexed_inputs: List[Dict], data: str) -> Dict:
    types = [input["type"] for input in non_indexed_inputs]
    values = decode(types, bytes.fromhex(data[2:]))
    return dict(zip((input["name"] for input in non_indexed_inputs), values))


def merge_parameters(indexed_values: Dict, non_indexed_values: Dict) -> Dict:
    merged = indexed_values.copy()
    merged.update(non_indexed_values)
    # Add __idx_ keys
    for idx, key in enumerate(chain(indexed_values.keys(), non_indexed_values.keys())):
        merged[f"__idx_{idx}"] = merged[key]
    return merged


def convert_bytes_to_hex(parameters: Dict) -> None:
    for key, val in list(parameters.items()):  # using list to prevent runtime error
        if isinstance(val, (bytes, bytearray)):
            parameters[key] = val.hex()
        elif isinstance(val, tuple):
            parameters[key] = tuple(e.hex() for e in val)


if __name__ == "__main__":
    import json

    abi = {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "sender",
                "type": "address",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount0In",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount1In",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount0Out",
                "type": "uint256",
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount1Out",
                "type": "uint256",
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "to",
                "type": "address",
            },
        ],
        "name": "Swap",
        "type": "event",
    }
    topics = [
        "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
        "0x0000000000000000000000007a250d5630b4cf539739df2c5dacb4c659f2488d",
        "0x0000000000000000000000007000042970cbbd3c1647f9e095561446d4afc79b",
    ]
    data = "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000c726dcc4b0c40000000000000000000000000000000000000000027494a5e0fb4fccba605fef3000000000000000000000000000000000000000000000000000000000000000000"  # noqa
    func_name, parameter = eth_decode_log(abi, topics, data)

    print(func_name)
    # Swap(address sender, address to, uint256 amount0In, uint256 amount1In, uint256 amount0Out, uint256 amount1Out) # noqa
    print(json.dumps(parameter, indent=2))
    # {
    #     "sender": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
    #     "to": "0x7000042970cbbd3c1647f9e095561446d4afc79b",
    #     "amount0In": 0,
    #     "amount1In": 896900000000000000,
    #     "amount0Out": 3112580648476110912111228416768,
    #     "amount1Out": 0,
    #     "__idx_0": "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
    #     "__idx_1": "0x7000042970cbbd3c1647f9e095561446d4afc79b",
    #     "__idx_2": 0,
    #     "__idx_3": 896900000000000000,
    #     "__idx_4": 3112580648476110912111228416768,
    #     "__idx_5": 0,
    # }
