from events import EventLogsDecoder
from events import (
    UniswapV2Decoder,
    UniswapV3Decoder,
    AAVEV3Decoder,
    AAVEV2Decoder,
    CompoundV3Decoder,
)
from model import Log
from multicall import Multicall
import pandas as pd
import logging
from typing import Dict


logger = logging.getLogger("EventDecoder[Test]")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(name)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

if __name__ == "__main__":
    df = pd.read_csv("func_sign.csv")

    mc = Multicall("https://mainnet.infura.io/v3/84842078b09946638c03157f83405213")
    uniswap_v2 = UniswapV2Decoder(mc=mc, logger=logger)
    uniswap_v3 = UniswapV3Decoder(mc=mc, logger=logger)
    aave_v2 = AAVEV2Decoder(mc=mc, logger=logger)
    aave_v3 = AAVEV3Decoder(mc=mc, logger=logger)
    compoundv3 = CompoundV3Decoder(mc=mc, logger=logger)

    evt_decoder = EventLogsDecoder(evt_df=df, verbose=True, logger=logger)
    evt_decoder.register_class(uniswap_v2)
    evt_decoder.register_class(uniswap_v3)
    evt_decoder.register_class(aave_v2)
    evt_decoder.register_class(aave_v3)
    evt_decoder.register_class(compoundv3)

    # Uniswap V2 Swap
    uniswap_v2_swap = Log()
    uniswap_v2_swap.address = "0x6adb403912608ffffd8fe623a7db35f59e4b4f43"
    uniswap_v2_swap.topics = [
        "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
        "0x0000000000000000000000007a250d5630b4cf539739df2c5dacb4c659f2488d",
        "0x0000000000000000000000003f96a535f9d31cbc59bd66caf4719bfd392c9e31",
    ]
    uniswap_v2_swap.data = "0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000016345785d8a000000000000000000000000000000000000000000000000000000003d9bd8bd21ce0000000000000000000000000000000000000000000000000000000000000000"

    # Uniswap V3 Swap
    uniswap_v3_swap = Log()
    uniswap_v3_swap.address = "0xeb9bd08ab9d518f6b03ed93cf1a14052fea68835"
    uniswap_v3_swap.topics = [
        "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67",
        "0x0000000000000000000000006b75d8af000000e20b7a7ddf000ba900b4009a80",
        "0x0000000000000000000000006b75d8af000000e20b7a7ddf000ba900b4009a80",
    ]
    uniswap_v3_swap.data = "0x00000000000000000000000000000000000000000039f6332a9c0bd755988e6afffffffffffffffffffffffffffffffffffffffffffffffffd1af5650f2c440e0000000000000000000000000000000000000000000393177f6dd74850db383f00000000000000000000000000000000000000000000e18490c9923025a573cafffffffffffffffffffffffffffffffffffffffffffffffffffffffffffd010c"

    # AAVE V2 Borrow
    aave_v2_borrow = Log()
    aave_v2_borrow.address = "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9"
    aave_v2_borrow.topics = [
        "0xc6a898309e823ee50bac64e45ca8adba6690e99e7841c45d754e2a38e9019d9b",
        "0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "0x0000000000000000000000008e1493554901ae0e5cfd17bfb5a860e6a21a1901",
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    ]
    aave_v2_borrow.data = "0x0000000000000000000000008e1493554901ae0e5cfd17bfb5a860e6a21a190100000000000000000000000000000000000000000000000000000073404c960000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000001fcd94a42b254519d5c8c1"

    # AAVE V2 Deposit
    aave_v2_deposit = Log()
    aave_v2_deposit.address = "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9"
    aave_v2_deposit.topics = [
        "0xc6a898309e823ee50bac64e45ca8adba6690e99e7841c45d754e2a38e9019d9b",
        "0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "0x0000000000000000000000008e1493554901ae0e5cfd17bfb5a860e6a21a1901",
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    ]
    aave_v2_deposit.data = "0x0000000000000000000000008e1493554901ae0e5cfd17bfb5a860e6a21a190100000000000000000000000000000000000000000000000000000073404c960000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000001fcd94a42b254519d5c8c1"

    # AAVE V2 Withdraw
    aave_v2_withdraw = Log()
    aave_v2_withdraw.address = "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9"
    aave_v2_withdraw.topics = [
        "0x3115d1449a7b732c986cba18244e897a450f61e1bb8d589cd2e69e6c8924f9f7",
        "0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "0x000000000000000000000000d76870037e89dd43b1ab14917267e7b47c124271",
        "0x000000000000000000000000d76870037e89dd43b1ab14917267e7b47c124271",
    ]
    aave_v2_withdraw.data = (
        "0x0000000000000000000000000000000000000000000000000000000ca1b2f733"
    )

    # AAVE V2 Repay
    aave_v2_repay = Log()
    aave_v2_repay.address = "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9"
    aave_v2_repay.topics = [
        "0x4cdde6e09bb755c9a5589ebaec640bbfedff1362d4b255ebf8339782b9942faa",
        "0x0000000000000000000000005f98805a4e8be255a32880fdec7f6728c6568ba0",
        "0x000000000000000000000000d968efc3420a063c3f9625bdce371559845d1681",
        "0x000000000000000000000000d968efc3420a063c3f9625bdce371559845d1681",
    ]
    aave_v2_repay.data = (
        "0x00000000000000000000000000000000000000000000001b1ae4d6e2ef500000"
    )

    # AAVE V2 Flash Loan
    aave_v2_flash_loan = Log()
    aave_v2_flash_loan.address = "0x7d2768de32b0b80b7a3454c06bdac94a69ddc7a9"
    aave_v2_flash_loan.topics = [
        "0x631042c832b07452973831137f2d73e395028b44b250dedc5abb0ee766e168ac",
        "0x000000000000000000000000135896de8421be2ec868e0b811006171d9df802a",
        "0x000000000000000000000000f46dc420de3feda15093e33fd3a83b8bff65b9bf",
        "0x000000000000000000000000c02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",
    ]
    aave_v2_flash_loan.data = "0x000000000000000000000000000000000000000000000000a816b539243230800000000000000000000000000000000000000000000000000026ba466d0303c80000000000000000000000000000000000000000000000000000000000000000"

    # AAVE V3 Supply
    aave_v3_supply = Log()
    aave_v3_supply.address = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
    aave_v3_supply.topics = [
        "0x2b627736bca15cd5381dcf80b0bf11fd197d01a037c52b927a881a10fb73ba61",
        "0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "0x0000000000000000000000002d759e9e4c1bb2a5d175faf2ed9f83712ac2b81c",
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    ]
    aave_v3_supply.data = "0x0000000000000000000000002d759e9e4c1bb2a5d175faf2ed9f83712ac2b81c00000000000000000000000000000000000000000000000000000000ac4a2f39"

    # AAVE V3 Borrow
    aave_v3_borrow = Log()
    aave_v3_borrow.address = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
    aave_v3_borrow.topics = [
        "0xb3d084820fb1a9decffb176436bd02558d15fac9b0ddfed8c465bc7359d7dce0",
        "0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "0x0000000000000000000000000ca7e7e5745bd457f5ed7265ff2cd1c8208575e1",
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    ]
    aave_v3_borrow.data = "0x0000000000000000000000000ca7e7e5745bd457f5ed7265ff2cd1c8208575e100000000000000000000000000000000000000000000000000000002540be40000000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000001bea5d9704c10e5d637c69"  # noqa

    # AAVE V3 Deposit
    aave_v3_deposit = Log()
    aave_v3_deposit.address = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"

    # AAVE V3 Withdraw
    aave_v3_withdraw = Log()
    aave_v3_withdraw.address = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
    aave_v3_withdraw.topics = [
        "0x3115d1449a7b732c986cba18244e897a450f61e1bb8d589cd2e69e6c8924f9f7",
        "0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "0x000000000000000000000000e42db4cfc31eb8a46442728418c6826ee31b3298",
        "0x000000000000000000000000e42db4cfc31eb8a46442728418c6826ee31b3298",
    ]
    aave_v3_withdraw.data = (
        "0x0000000000000000000000000000000000000000000000000000000e666ba74f"
    )

    # AAVE V3 Repay
    aave_v3_repay = Log()
    aave_v3_repay.address = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
    aave_v3_repay.topics = [
        "0xa534c8dbe71f871f9f3530e97a74601fea17b426cae02e1c5aee42c96c784051",
        "0x000000000000000000000000dac17f958d2ee523a2206206994597c13d831ec7",
        "0x0000000000000000000000006258fe88db0dbd0bd67d4c323a82e7d5c6a4d194",
        "0x0000000000000000000000006258fe88db0dbd0bd67d4c323a82e7d5c6a4d194",
    ]
    aave_v3_repay.data = "0x00000000000000000000000000000000000000000000000000000000b87ed5c00000000000000000000000000000000000000000000000000000000000000000"  # noqa

    # AAVE V3 Flash Loan
    aave_v3_flash_loan = Log()
    aave_v3_flash_loan.address = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
    aave_v3_flash_loan.topics = [
        "0xefefaba5e921573100900a3ad9cf29f222d995fb3b6045797eaea7521bd8d6f0",
        "0x000000000000000000000000adc0a53095a0af87f3aa29fe0715b5c28016364e",
        "0x0000000000000000000000002260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    ]
    aave_v3_flash_loan.data = "0x000000000000000000000000f52e602be034b221d5d56aa544f2df71d92fe77d0000000000000000000000000000000000000000000000000000000002faf080000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000061a8"

    # AAVE V3 Collateral Enabled
    aave_v3_collateral_enabled = Log()
    aave_v3_collateral_enabled.address = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
    aave_v3_collateral_enabled.topics = [
        "0x44c58d81365b66dd4b1a7f36c25aa97b8c71c361ee4937adc1a00000227db5dd",
        "0x0000000000000000000000002260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "0x000000000000000000000000adc0a53095a0af87f3aa29fe0715b5c28016364e",
    ]
    aave_v3_collateral_enabled.data = "0x"

    # AAVE V3 Collateral Disabled
    aave_v3_collateral_disabled = Log()
    aave_v3_collateral_disabled.address = "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
    aave_v3_collateral_disabled.topics = [
        "0x44c58d81365b66dd4b1a7f36c25aa97b8c71c361ee4937adc1a00000227db5dd",
        "0x0000000000000000000000002260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "0x000000000000000000000000adc0a53095a0af87f3aa29fe0715b5c28016364e",
    ]
    aave_v3_collateral_disabled.data = "0x"

    # Compound V3 Supply
    compound_v3_supply = Log()
    compound_v3_supply.address = "0xc3d688b66703497daa19211eedff47f25384cdc3"
    compound_v3_supply.topics = [
        "0xd1cf3d156d5f8f0d50f6c122ed609cec09d35c9b9fb3fff6ea0959134dae424e",
        "0x00000000000000000000000004333a1788a47068b9102d2d35695c312a0b312f",
        "0x00000000000000000000000004333a1788a47068b9102d2d35695c312a0b312f",
    ]
    compound_v3_supply.data = (
        "0x0000000000000000000000000000000000000000000000000000000000989680"
    )

    # Compound V3 Supply Collateral
    compound_v3_supply_collateral = Log()
    compound_v3_supply_collateral.address = "0xc3d688b66703497daa19211eedff47f25384cdc3"
    compound_v3_supply_collateral.topics = [
        "0xfa56f7b24f17183d81894d3ac2ee654e3c26388d17a28dbd9549b8114304e1f4",
        "0x0000000000000000000000000688547a2b5f07327a7a2644fb649caa29c730eb",
        "0x0000000000000000000000000688547a2b5f07327a7a2644fb649caa29c730eb",
        "0x0000000000000000000000001f9840a85d5af5bf1d1762f925bdaddc4201f984",
    ]
    compound_v3_supply_collateral.data = (
        "0x00000000000000000000000000000000000000000000000821ab0d4414980000"
    )

    # Compound V3 Withdraw
    compound_v3_withdraw = Log()
    compound_v3_withdraw.address = "0xc3d688b66703497daa19211eedff47f25384cdc3"
    compound_v3_withdraw.topics = [
        "0x9b1bfa7fa9ee420a16e124f794c35ac9f90472acc99140eb2f6447c714cad8eb",
        "0x000000000000000000000000c34c261158fd908bb7a577f15d3a3d0ff8263513",
        "0x000000000000000000000000c34c261158fd908bb7a577f15d3a3d0ff8263513",
    ]
    compound_v3_withdraw.data = (
        "0x0000000000000000000000000000000000000000000000000000000005f5e100"
    )

    test_cases: Dict[str, Log] = {
        # "Uniswap V2 Swap": uniswap_v2_swap,
        # "Uniswap V3 Swap": uniswap_v3_swap,
        # #
        # "AAVE V2 Deposit": aave_v2_deposit,
        # "AAVE V2 Borrow": aave_v2_borrow,
        # "AAVE V2 Withdraw": aave_v2_withdraw,
        # "AAVE V2 Repay": aave_v2_repay,
        # "AAVE V2 Flash Loan": aave_v2_flash_loan,
        # #
        # "AAVE V3 Supply": aave_v3_supply,
        # "AAVE V3 Borrow": aave_v3_borrow,
        # "AAVE V3 Withdraw": aave_v3_withdraw,
        # "AAVE V3 Repay": aave_v3_repay,
        # "AAVE V3 Flash Loan": aave_v3_flash_loan,
        # "AAVE V3 Collateral Enabled": aave_v3_collateral_enabled,
        # "AAVE V3 Collateral Disabled": aave_v3_collateral_disabled,
        # #
        # "Compound V3 Supply": compound_v3_supply,
        # "Compound V3 Supply Collateral": compound_v3_supply_collateral,
        "Compound V3 Withdraw": compound_v3_withdraw,
    }

    for name, test_case in test_cases.items():
        decoded = evt_decoder.decode(test_case)
        print("Test Case: ", name)
        print(decoded)
        print()
