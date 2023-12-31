from typing import Callable, Dict, TypedDict, List, Tuple, Union
from model import Log
from utils import get_addr_entry
import pandas as pd
import logging
import json
from multicall import Multicall, Call
import logging
from type import LogDict
from typing import Dict, List, Tuple, Union
from itertools import chain
from eth_abi import decode
from concurrent.futures import ThreadPoolExecutor

HandleEventFunc = Callable[[Dict], str]
EventPayload = TypedDict("EventPayload", {"address": str, "params": Dict})


def eth_decode_log(event_abi: Dict, topics: List[str], data: str) -> Tuple[str, Dict]:
    """
    Decodes Ethereum log given the event ABI, topics, and data.

    Parameters
    ----------
    event_abi : Dict
        The ABI of the event.
    topics : List[str]
        The topics associated with the log.
    data : str
        The data associated with the log.

    Returns
    -------
    Tuple[str, Dict]
        The function signature and the parameters decoded from the log.

    """

    # Ensure ABI is a valid event
    if "name" not in event_abi or event_abi.get("type") != "event":
        return "{}", {}

    # Separate indexed and non-indexed inputs
    indexed_inputs, non_indexed_inputs = _partition_inputs(event_abi.get("inputs", []))

    func_signature = _create_function_signature(
        event_abi["name"], indexed_inputs + non_indexed_inputs
    )

    indexed_values = _decode_values_from_topics(indexed_inputs, topics)
    non_indexed_values = _decode_values_from_data(non_indexed_inputs, data)

    # Merge indexed and non-indexed values
    parameters = _merge_parameters(indexed_values, non_indexed_values)

    # Convert byte data to hex
    _convert_bytes_to_hex(parameters)

    return func_signature, parameters


def _partition_inputs(inputs: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Partitions inputs into indexed and non-indexed inputs.

    Parameters
    ----------
    inputs : List[Dict]
        List of inputs from ABI.

    Returns
    -------
    Tuple[List[Dict], List[Dict]]
        A tuple containing indexed and non-indexed inputs.

    """
    indexed, non_indexed = [], []
    for input in inputs:
        if input.get("indexed"):
            indexed.append(input)
        else:
            non_indexed.append(input)
    return indexed, non_indexed


def _create_function_signature(name: str, inputs: List[Dict]) -> str:
    """
    Creates a function signature string based on the name and inputs.

    Parameters
    ----------
    name : str
        Name of the function.
    inputs : List[Dict]
        List of inputs associated with the function.

    Returns
    -------
    str
        The function signature.

    """
    return "{}({})".format(
        name,
        ", ".join([f"{input['type']} {input.get('name', '')}" for input in inputs]),
    )


def _decode_values_from_topics(indexed_inputs: List[Dict], topics: List[str]) -> Dict:
    """
    Decodes values from topics based on indexed inputs.

    Parameters
    ----------
    indexed_inputs : List[Dict]
        List of indexed inputs.
    topics : List[str]
        List of topics.

    Returns
    -------
    Dict
        A dictionary of decoded values from topics.

    """
    return {
        input["name"]: decode([input["type"]], bytes.fromhex(topic[2:]))[0]
        for input, topic in zip(indexed_inputs, topics[1:])
    }


def _decode_values_from_data(non_indexed_inputs: List[Dict], data: str) -> Dict:
    """
    Decodes values from data based on non-indexed inputs.

    Parameters
    ----------
    non_indexed_inputs : List[Dict]
        List of non-indexed inputs.
    data : str
        The associated data.

    Returns
    -------
    Dict
        A dictionary of decoded values from data.

    """
    types = [input["type"] for input in non_indexed_inputs]
    values = decode(types, bytes.fromhex(data[2:]))
    return dict(zip((input["name"] for input in non_indexed_inputs), values))


def _merge_parameters(indexed_values: Dict, non_indexed_values: Dict) -> Dict:
    """
    Merges indexed and non-indexed values, and adds index keys.

    Parameters
    ----------
    indexed_values : Dict
        A dictionary of indexed values.
    non_indexed_values : Dict
        A dictionary of non-indexed values.

    Returns
    -------
    Dict
        A merged dictionary of indexed and non-indexed values with index keys.

    """
    merged = indexed_values.copy()
    merged.update(non_indexed_values)
    # Add __idx_ keys
    for idx, key in enumerate(chain(indexed_values.keys(), non_indexed_values.keys())):
        merged[f"__idx_{idx}"] = merged[key]
    return merged


def _convert_bytes_to_hex(parameters: Dict) -> None:
    """
    Converts bytes data in the parameters dictionary to hexadecimal. (INPLACE)

    Parameters
    ----------
    parameters : Dict
        The dictionary containing parameters.

    Returns
    -------
    None

    """
    for key, val in list(parameters.items()):  # using list to prevent runtime error
        if isinstance(val, (bytes, bytearray)):
            parameters[key] = val.hex()
        elif isinstance(val, tuple):
            parameters[key] = tuple(e.hex() for e in val)


class BaseDecoder:
    def __init__(
        self,
        mc: Multicall,
        logger: logging.Logger = None,
    ):
        self.mc = mc
        self.logger = logger

    def _get_token_decimals(self, addrs: Union[List[str], str]) -> List[int]:
        if isinstance(addrs, str):
            addrs = [addrs]

        calls = [Call(target=addr, function="decimals()(uint8)") for addr in addrs]

        result = self.mc.agg(calls)
        return [item["result"] for item in result]


class BaseUniswapDecoder(BaseDecoder):
    def _get_token_pair(self, pool_addr: str) -> Tuple[str, str]:
        result = self.mc.agg(
            [
                Call(
                    target=pool_addr,
                    function="token0()(address)",
                    request_id="token0",
                ),
                Call(
                    target=pool_addr,
                    function="token1()(address)",
                    request_id="token1",
                ),
            ]
        )
        token_map = {item["request_id"]: item["result"] for item in result}
        return token_map["token0"], token_map["token1"]


class UniswapV2Decoder(BaseUniswapDecoder):
    def __init__(
        self,
        mc: Multicall,
        logger: logging.Logger = None,
    ) -> None:
        super().__init__(mc, logger)

    def swap(self) -> Tuple[str, HandleEventFunc]:
        # Swap(address indexed sender,uint amount0In, uint amount1In, uint amount0Out, uint amount1Out, address indexed to);
        event_sig = "Swap(address,uint256,uint256,uint256,uint256,address)"

        def decoder(payload: EventPayload) -> str:
            template = "Swap {get_amount} {get_token} for {pay_amount} {pay_token}  on UniswapV2"
            token0_addr, token1_addr = self._get_token_pair(payload["address"])
            token0_decimals, token1_decimals = self._get_token_decimals(
                [token0_addr, token1_addr]
            )
            params = payload["params"]
            amount0_diff = int(params["amount0Out"]) - int(params["amount0In"])
            amount1_diff = int(params["amount1Out"]) - int(params["amount1In"])
            if amount0_diff > 0:
                return template.format(
                    pay_amount=abs(amount0_diff / 10**token0_decimals),
                    pay_token=get_addr_entry(token0_addr),
                    get_amount=abs(amount1_diff / 10**token1_decimals),
                    get_token=get_addr_entry(token1_addr),
                )
            else:
                return template.format(
                    pay_amount=abs(amount1_diff / 10**token1_decimals),
                    pay_token=get_addr_entry(token1_addr),
                    get_amount=abs(amount0_diff / 10**token0_decimals),
                    get_token=get_addr_entry(token0_addr),
                )

        return event_sig, decoder

    def pair_created(self) -> tuple[str, HandleEventFunc]:
        # PairCreated(address indexed token0, address indexed token1, address pair, uint);
        event_sig = "PairCreated(address,address,address,uint256)"

        def decoder(payload: EventPayload) -> str:
            token0 = get_addr_entry(payload["params"]["token0"])
            token1 = get_addr_entry(payload["params"]["token1"])
            return f"Created {token0}/{token1} pair"

        return event_sig, decoder

    def mint(self) -> tuple[str, HandleEventFunc]:
        # Mint(address indexed sender, uint amount0, uint amount1);
        event_sig = "Mint(address,uint256,uint256)"

        def decoder(payload: EventPayload) -> str:
            token0_addr, token1_addr = self._get_token_pair(payload["address"])
            token0_decimals, token1_decimals = self._get_token_decimals(
                [token0_addr, token1_addr]
            )
            params = payload["params"]
            return ""

        return event_sig, decoder

    def burn(self) -> tuple[str, HandleEventFunc]:
        # Burn(address indexed sender, uint amount0, uint amount1, address indexed to);
        event_sig = "Burn(address,uint256,uint256,address)"

        def decoder(payload: EventPayload) -> str:
            token0_addr, token1_addr = self._get_token_pair(payload["address"])
            token0_decimals, token1_decimals = self._get_token_decimals(
                [token0_addr, token1_addr]
            )
            params = payload["params"]
            return ""

        return event_sig, decoder


class UniswapV3Decoder(BaseUniswapDecoder):
    """
    https://docs.uniswap.org/contracts/v3/reference/core/interfaces/pool/IUniswapV3PoolEvents
    """

    def __init__(self, mc: Multicall, logger: logging.Logger = None):
        super().__init__(mc, logger)

    def _get_tokens_by_position(self, pool_addr: str, pos_id: int) -> Tuple[str, str]:
        result = self.mc.agg(
            [
                Call(
                    target=pool_addr,
                    function="positions(uint256)(uint96,address,address,address,uint24,int24,int24,uint128,uint256,uint256,uint128,uint128)",
                    args=[pos_id],
                    request_id="positions",
                ),
            ]
        )
        if len(result) != 1:
            raise ValueError(f"Cannot find position {pos_id} in {pool_addr}")
        result = result[0]["result"]
        token0_addr, token1_addr = result[2], result[3]
        return token0_addr, token1_addr

    def pool_created(self) -> tuple[str, HandleEventFunc]:
        # PoolCreated(address token0,address token1,uint24 fee,int24 tickSpacing,address pool)
        event_sig = "PoolCreated(address,address,uint24,int24,address)"

        def decoder(payload: EventPayload) -> str:
            token0 = get_addr_entry(payload["params"]["token0"])
            token1 = get_addr_entry(payload["params"]["token1"])
            return f"Created {token0}/{token1} pool with {payload['params']['fee']/ 100}% fee"

        return event_sig, decoder

    def increase_liquidity(self) -> tuple[str, HandleEventFunc]:
        # IncreaseLiquidity(uint256 indexed tokenId, uint128 liquidity, uint256 amount0, uint256 amount1);
        event_sig = "IncreaseLiquidity(uint256,uint128,uint256,uint256)"

        def decoder(payload: EventPayload) -> str:
            template = (
                "Add {amount0} {token0} and {amount1} {token1} liquidity to {pool}"
            )
            params = payload["params"]
            token0_addr, token1_addr = self._get_tokens_by_position(
                payload["address"], params["tokenId"]
            )
            token0_decimals, token1_decimals = self._get_token_decimals(
                [token0_addr, token1_addr]
            )
            return template.format(
                amount0=abs(int(params["amount0"]) / 10**token0_decimals),
                token0=get_addr_entry(token0_addr),
                amount1=abs(int(params["amount1"]) / 10**token1_decimals),
                token1=get_addr_entry(token1_addr),
                pool=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def decrease_liquidity(self) -> tuple[str, HandleEventFunc]:
        # DecreaseLiquidity(uint256 indexed tokenId, uint128 liquidity, uint256 amount0, uint256 amount1);
        event_sig = "DecreaseLiquidity(uint256,uint128,uint256,uint256)"

        def decoder(payload: EventPayload) -> str:
            template = (
                "Remove {amount0} {token0} and {amount1} {token1} liquidity from {pool}"
            )
            token0_addr, token1_addr = self._get_tokens_by_position(payload["address"])
            token0_decimals, token1_decimals = self._get_token_decimals(
                [token0_addr, token1_addr]
            )
            params = payload["params"]
            return template.format(
                amount0=abs(int(params["amount0"]) / 10**token0_decimals),
                token0=get_addr_entry(token0_addr),
                amount1=abs(int(params["amount1"]) / 10**token1_decimals),
                token1=get_addr_entry(token1_addr),
                pool=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def swap(self) -> tuple[str, HandleEventFunc]:
        # Swap(address sender,address recipient,int256 amount0,int256 amount1,uint160 sqrtPriceX96,uint128 liquidity,int24 tick)
        event_sig = "Swap(address,address,int256,int256,uint160,uint128,int24)"

        def decoder(payload: EventPayload) -> str:
            template = "Swap {pay_amount} {pay_token} for {get_amount} {get_token} on UniswapV3"
            token0_addr, token1_addr = self._get_token_pair(payload["address"])
            token0, token1 = get_addr_entry(token0_addr), get_addr_entry(token1_addr)
            amount0, amount1 = (
                payload["params"]["amount0"],
                payload["params"]["amount1"],
            )
            token0_decimals, token1_decimals = self._get_token_decimals(
                [token0_addr, token1_addr]
            )
            if int(amount0) > 0:
                return template.format(
                    pay_amount=abs(int(amount0) / 10**token0_decimals),
                    pay_token=token0,
                    get_amount=abs(int(amount1) / 10**token1_decimals),
                    get_token=token1,
                )
            else:
                return template.format(
                    pay_amount=abs(int(amount1) / 10**token1_decimals),
                    pay_token=token1,
                    get_amount=abs(int(amount0) / 10**token0_decimals),
                    get_token=token0,
                )

        return event_sig, decoder

    def flash(self) -> tuple[str, HandleEventFunc]:
        # Flash(address sender, address recipient, uint256 amount0, uint256 amount1 ,uint256 paid0, uint256 paid1)
        event_sig = "Flash(address,address,uint256,uint256,uint256,uint256)"

        def decoder(payload: EventPayload) -> str:
            template = "Flashloan {flash_stmt} then repay {repay_stmt}"
            token0_addr, token1_addr = self._get_token_pair(payload["address"])
            token0, token1 = get_addr_entry(token0_addr), get_addr_entry(token1_addr)
            token0_decimals, token1_decimals = self._get_token_decimals(
                [token0_addr, token1_addr]
            )
            amount0, amount1, paid0, paid1 = (
                payload["params"]["amount0"] / 10**token0_decimals,
                payload["params"]["amount1"] / 10**token1_decimals,
                payload["params"]["paid0"] / 10**token0_decimals,
                payload["params"]["paid1"] / 10**token1_decimals,
            )
            flash_stmt = []
            if amount0 > 0:
                flash_stmt.append(f"{amount0} {token0}")
            if amount1 > 0:
                flash_stmt.append(f"{amount1} {token1}")

            repay_stmt = []
            if paid0 > 0:
                repay_stmt.append(f"{paid0} {token0}")
            if paid1 > 0:
                repay_stmt.append(f"{paid1} {token1}")

            return template.format(
                flash_stmt=" and ".join(flash_stmt),
                repay_stmt=" and ".join(repay_stmt),
            )

        return event_sig, decoder

    def collect(self) -> tuple[str, HandleEventFunc]:
        # Collect(address owner,int24 tickLower,int24 tickUpper,uint128 amount0,uint128 amount1)
        event_sig = "Collect(address,int24,int24,uint128,uint128)"

        def decoder(payload: EventPayload) -> str:
            template = (
                "Collect {amount0} {token0} and {amount1} {token1} fees from {pool}"
            )
            token0_addr, token1_addr = self._get_token_pair(payload["address"])
            token0_decimals, token1_decimals = self._get_token_decimals(
                [token0_addr, token1_addr]
            )
            params = payload["params"]
            return template.format(
                amount0=abs(int(params["amount0"]) / 10**token0_decimals),
                token0=get_addr_entry(token0_addr),
                amount1=abs(int(params["amount1"]) / 10**token1_decimals),
                token1=get_addr_entry(token1_addr),
                pool=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def owner_changed(self) -> tuple[str, HandleEventFunc]:
        # OwnerChanged(address oldOwner, address newOwner)
        event_sig = "OwnerChanged(address,address)"

        def decoder(payload: EventPayload) -> str:
            return f"Change owner of {payload['address']} from {payload['params']['oldOwner']} to {payload['params']['newOwner']}"

        return event_sig, decoder


class AAVEV2Decoder(BaseDecoder):
    def __init__(self, mc: Multicall, logger: logging.Logger = None):
        super().__init__(mc, logger)

    def deposit(self) -> Tuple[str, HandleEventFunc]:
        # Deposit (index_topic_1 address reserve, address user, index_topic_2 address onBehalfOf, uint256 amount, index_topic_3 uint16 referral)
        event_sig = "Deposit(address,address,address,uint256,uint16)"

        def decoder(payload: EventPayload) -> str:
            template = "Deposit {amount} {token} to {protocol}"
            token_addr = payload["params"]["reserve"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            amount = payload["params"]["amount"] / 10**token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def borrow(self) -> Tuple[str, HandleEventFunc]:
        # Borrow (index_topic_1 address reserve, address user, index_topic_2 address onBehalfOf, uint256 amount, uint256 borrowRateMode, uint256 borrowRate, index_topic_3 uint16 referral)
        event_sig = "Borrow(address,address,address,uint256,uint256,uint256,uint16)"

        def decoder(payload: EventPayload) -> str:
            template = "Borrow {amount} {token} from {protocol}"
            token_addr = payload["params"]["reserve"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            amount = payload["params"]["amount"] / 10**token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def withdraw(self) -> Tuple[str, HandleEventFunc]:
        # Withdraw (index_topic_1 address reserve, index_topic_2 address user, index_topic_3 address to, uint256 amount)
        event_sig = "Withdraw(address,address,address,uint256)"

        def decoder(payload: EventPayload) -> str:
            template = "Withdraw {amount} {token} from {protocol}"
            token_addr = payload["params"]["reserve"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            amount = payload["params"]["amount"] / 10**token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def repay(self) -> Tuple[str, HandleEventFunc]:
        # Repay (index_topic_1 address reserve, index_topic_2 address user, index_topic_3 address repayer, uint256 amount)
        event_sig = "Repay(address,address,address,uint256)"

        def decoder(payload: EventPayload) -> str:
            template = "Repay {amount} {token} to {protocol}"
            token_addr = payload["params"]["reserve"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            amount = payload["params"]["amount"] / 10**token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def flashloan(self) -> Tuple[str, HandleEventFunc]:
        # FlashLoan (index_topic_1 address target, index_topic_2 address initiator, index_topic_3 address asset, uint256 amount, uint256 premium, uint16 referralCode)
        event_sig = "FlashLoan(address,address,address,uint256,uint256,uint16)"

        def decoder(payload: EventPayload) -> str:
            template = "Flashloan {amount} {token} from {protocol}"
            token_addr = payload["params"]["asset"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            amount = payload["params"]["amount"] / 10**token_decimals

            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder


class AAVEV3Decoder(BaseDecoder):
    """
    Refs:
    https://etherscan.io/address/0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2
    """

    def __init__(self, mc: Multicall, logger: logging.Logger = None):
        super().__init__(mc, logger)

    def supply(self) -> Tuple[str, HandleEventFunc]:
        # Supply (index_topic_1 address reserve, address user, index_topic_2 address onBehalfOf, uint256 amount, index_topic_3 uint16 referralCode)
        event_sig = "Supply(address,address,address,uint256,uint16)"

        def decoder(payload: EventPayload) -> str:
            template = "Supply {amount} {token} to {protocol}"
            token_addr = payload["params"]["reserve"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            amount = payload["params"]["amount"] / 10**token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def borrow(self) -> Tuple[str, HandleEventFunc]:
        # Borrow (index_topic_1 address reserve, address user, index_topic_2 address onBehalfOf, uint256 amount, uint8 interestRateMode, uint256 borrowRate, index_topic_3 uint16 referralCode)
        event_sig = "Borrow(address,address,address,uint256,uint8,uint256,uint16)"

        def decoder(payload: EventPayload) -> str:
            template = "Borrow {amount} {token} from {protocol}"
            token_addr = payload["params"]["reserve"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            amount = payload["params"]["amount"] / 10**token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def withdraw(self) -> Tuple[str, HandleEventFunc]:
        # Withdraw (index_topic_1 address reserve, index_topic_2 address user, index_topic_3 address to, uint256 amount)
        event_sig = "Withdraw(address,address,address,uint256)"

        def decoder(payload: EventPayload) -> str:
            template = "Withdraw {amount} {token} from {protocol}"
            token_addr = payload["params"]["reserve"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            amount = payload["params"]["amount"] / 10**token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def flashloan(self) -> Tuple[str, HandleEventFunc]:
        # FlashLoan(address indexed target, address initiator, address indexed asset, uint256 amount, DataTypes.InterestRateMode interestRateMode, uint256 premium, uint16 indexed referralCode);
        # Custon Type DataTypes.InterestRateMode is an enum, so we use uint8 to represent it
        event_sig = "FlashLoan(address,address,address,uint256,uint8,uint256,uint16)"

        def decoder(payload: EventPayload) -> str:
            template = "Flashloan {amount} {token} from {protocol}"
            token_addr = payload["params"]["asset"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            amount = payload["params"]["amount"] / 10**token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def repay(self) -> Tuple[str, HandleEventFunc]:
        # event Repay(address indexed reserve, address indexed user, address indexed repayer, uint256 amount, bool useATokens);
        event_sig = "Repay(address,address,address,uint256,bool)"

        def decoder(payload: EventPayload) -> str:
            template = "Repay {amount} {token} to {protocol}"
            token_addr = payload["params"]["reserve"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            amount = payload["params"]["amount"] / 10**token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def reserve_used_as_collateral_enabled(self) -> Tuple[str, HandleEventFunc]:
        # ReserveUsedAsCollateralEnabled (index_topic_1 address reserve, index_topic_2 address user)
        event_sig = "ReserveUsedAsCollateralEnabled(address,address)"

        def decoder(payload: EventPayload) -> str:
            asset = get_addr_entry(payload["params"]["reserve"])
            addr = get_addr_entry(payload["address"])
            return f"Enable {asset} as collateral on {addr}"

        return event_sig, decoder

    def reserve_used_as_collateral_disabled(self) -> Tuple[str, HandleEventFunc]:
        # ReserveUsedAsCollateralDisabled (index_topic_1 address reserve, index_topic_2 address user)
        event_sig = "ReserveUsedAsCollateralDisabled(address,address)"

        def decoder(payload: EventPayload) -> str:
            asset = get_addr_entry(payload["params"]["reserve"])
            addr = get_addr_entry(payload["address"])
            return f"Disable {asset} as collateral on {addr}"

        return event_sig, decoder


class CompoundV3Decoder(BaseDecoder):
    def __init__(self, mc: Multicall, logger: logging.Logger = None):
        super().__init__(mc, logger)

    def supply_collateral(self) -> Tuple[str, HandleEventFunc]:
        # SupplyCollateral (index_topic_1 address from, index_topic_2 address dst, index_topic_3 address asset, uint256 amount)
        event_sig = "SupplyCollateral(address,address,address,uint256)"

        def decoder(payload: EventPayload) -> str:
            template = "Supply {amount} {token} as collateral to {protocol}"
            token_addr = payload["params"]["asset"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            amount = payload["params"]["amount"] / 10**token_decimals

            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder

    def withdraw(self) -> Tuple[str, HandleEventFunc]:
        # Withdraw (index_topic_1 address src, index_topic_2 address to, uint256 amount)
        event_sig = "Withdraw(address,address,uint256)"

        def decoder(payload: EventPayload) -> str:
            template = "Withdraw {amount} {token} to {reciver} on Compound"
            token_addr = payload["address"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            params = payload["params"]
            amount = params["__idx_2"] / 10**token_decimals
            recieiver = params["__idx_1"]
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                reciver=get_addr_entry(recieiver),
            )

        return event_sig, decoder

    def supply(self) -> Tuple[str, HandleEventFunc]:
        # Supply (index_topic_1 address from, index_topic_2 address dst, uint256 amount)
        event_sig = "Supply(address,address,uint256)"

        def decoder(payload: EventPayload) -> str:
            template = "Supply {amount} {token} to {dst} on Compound"
            token_addr = payload["address"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            params = payload["params"]
            amount = params["__idx_2"] / 10**token_decimals
            dst = params["__idx_1"]
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                dst=get_addr_entry(dst),
            )

        return event_sig, decoder


class BancorV3Decoder(BaseDecoder):
    def __init__(self, mc: Multicall, logger: logging.Logger = None):
        super().__init__(mc, logger)

    def tokens_traded(self) -> Tuple[str, HandleEventFunc]:
        # TokensTraded (index_topic_1 bytes32 contextId, index_topic_2 address sourceToken, index_topic_3 address targetToken, uint256 sourceAmount, uint256 targetAmount, uint256 bntAmount, uint256 targetFeeAmount, uint256 bntFeeAmount, address trader)
        event_sig = "TokensTraded(bytes32,address,address,uint256,uint256,uint256,uint256,uint256,address)"

        def decoder(payload: EventPayload) -> str:
            template = "Trade {amount} {token} for {get_amount} {get_token} on Bancor"
            token_addr = payload["params"]["sourceToken"]
            get_token_addr = payload["params"]["targetToken"]
            (token_decimals, get_token_decimals) = self._get_token_decimals(
                [token_addr, get_token_addr]
            )
            params = payload["params"]
            amount = params["sourceAmount"] / 10**token_decimals
            get_amount = params["targetAmount"] / 10**get_token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                get_amount=get_amount,
                get_token=get_addr_entry(get_token_addr),
            )

        return event_sig, decoder

    def funds_withdrawn(self) -> Tuple[str, HandleEventFunc]:
        # FundsWithdrawn (index_topic_1 address token, index_topic_2 address caller, index_topic_3 address target, uint256 amount)
        event_sig = "FundsWithdrawn(address,address,address,uint256)"

        def decoder(payload: EventPayload) -> str:
            template = "Withdraw {amount} {token} from {protocol}"
            token_addr = payload["params"]["token"]
            (token_decimals,) = self._get_token_decimals(token_addr)
            params = payload["params"]
            amount = params["amount"] / 10**token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                protocol=get_addr_entry(payload["address"]),
            )

        return event_sig, decoder


class CurveV2Decoder(BaseDecoder):
    def __init__(self, mc: Multicall, logger: logging.Logger = None):
        super().__init__(mc, logger)

    def token_exchange(self) -> Tuple[str, HandleEventFunc]:
        # TokenExchange (index_topic_1 address buyer, index_topic_2 address receiver, index_topic_3 address pool, address token_sold, address token_bought, uint256 amount_sold, uint256 amount_bought)
        event_sig = (
            "TokenExchange(address,address,address,address,address,uint256,uint256)"
        )

        def decoder(payload: EventPayload) -> str:
            template = "Exchange {amount} {token} for {get_amount} {get_token} on Curve"
            token_addr = payload["params"]["token_sold"]
            get_token_addr = payload["params"]["token_bought"]
            (token_decimals, get_token_decimals) = self._get_token_decimals(
                [token_addr, get_token_addr]
            )
            params = payload["params"]
            amount = params["amount_sold"] / 10**token_decimals
            get_amount = params["amount_bought"] / 10**get_token_decimals
            return template.format(
                amount=amount,
                token=get_addr_entry(token_addr),
                get_amount=get_amount,
                get_token=get_addr_entry(get_token_addr),
            )

        return event_sig, decoder


class EventLogsDecoder:
    def __init__(
        self,
        evt_df: pd.DataFrame,
        verbose: bool = False,
        logger: logging.Logger = None,
        *args,
        **kwargs,
    ) -> None:
        self.hdlrs: Dict[str, HandleEventFunc] = {}
        self.evt_df = evt_df

        self.logger = logger
        if logger is None and verbose:
            class_name = self.__class__.__name__
            self.logger = logging.getLogger(class_name)
            self.logger.setLevel(logging.DEBUG)
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(name)s | %(levelname)s | %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.verbose = verbose

    def register(self, byte_sign: str, handle_func: HandleEventFunc) -> None:
        if self.verbose:
            self.logger.info(f"Registering event {byte_sign}")
        self.hdlrs[byte_sign] = handle_func

    def register_class(self, cls: BaseDecoder) -> None:
        for attr in dir(cls):
            if attr.startswith("_"):
                continue
            handle_func = getattr(cls, attr)
            if not callable(handle_func):
                continue
            event_sig, decoder = handle_func()
            self.register(event_sig, decoder)

    def _get_abi_text_sign(self, byte_sign: str) -> Tuple[str, str]:
        filtered = self.evt_df["byte_sign"] == byte_sign
        candidate = self.evt_df[filtered][["abi", "text_sign"]].values
        if len(candidate) == 0:
            return "", ""
        return candidate[0]

    def decode(self, log: LogDict) -> str:
        topics = log.get("topics", [])

        if len(topics) == 0:
            raise ValueError("Log topics is empty")

        abi, text_sign = self._get_abi_text_sign(topics[0])

        handler = self.hdlrs.get(text_sign, None)
        if handler is None:
            return ""

        abi = json.loads(abi)
        try:
            _, params = eth_decode_log(abi, topics, log.get("data", "0x"))
            result = handler({"address": log["address"], "params": params})
            return result
        except Exception as e:
            if self.verbose:
                self.logger.error(
                    f"Failed to decode event {text_sign} with params {params}"
                )
                self.logger.exception(e)
            return ""

    def decode_all(self, logs: List[LogDict], workers: int = 10) -> List[str]:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            return list(executor.map(self.decode, logs))
