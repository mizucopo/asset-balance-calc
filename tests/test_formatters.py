"""フォーマット処理モジュールのテスト"""

from decimal import Decimal

from mizu_common import Asset, AssetAdjustmentResult, AssetCalculation

from src.formatters import AssetFormatter
from src.models.config import Config


def _make_calc(
    name: str = "株式",
    amount: Decimal = Decimal("60000000"),
    rate: Decimal = Decimal("0.6"),
    current_rate: Decimal = Decimal("0.6"),
    flow_amount: Decimal = Decimal("0"),
) -> AssetCalculation:
    """テスト用AssetCalculationを生成する"""
    return AssetCalculation(
        asset=Asset(name=name, amount=amount, rate=rate),
        current_rate=current_rate,
        flow_amount=flow_amount,
    )


def test_current_summary_generated_correctly(
    formatter: AssetFormatter,
) -> None:
    """現在のサマリーが生成されること

    Arrange
    - calculated_assetsを持つConfigを準備
    Act
    - format_current_summaryを実行
    Assert
    - サマリーに各資産情報が含まれること
    """
    # Arrange
    bond_calc = _make_calc(
        name="債券",
        amount=Decimal("40000000"),
        rate=Decimal("0.4"),
        current_rate=Decimal("0.4"),
    )
    config = Config(
        adjustment_amount=Decimal("0"),
        assets=(),
        calculated_assets=(_make_calc(), bond_calc),
    )
    adj_result = AssetAdjustmentResult(
        assets=tuple(calc.asset for calc in config.calculated_assets),
        calculated_assets=config.calculated_assets,
        adjustment_amount=Decimal("0"),
    )

    # Act
    result = formatter.format_current_summary(config, adj_result)

    # Assert
    assert "現在の資産配分" in result
    assert "株式" in result
    assert "債券" in result


def test_summaries_prioritize_larger_flow_amounts(
    formatter: AssetFormatter,
) -> None:
    """現在と調整後が入出金額の絶対値が大きい銘柄順で出力されること

    Arrange
    - 設定順と入出金額順が異なり、同額の銘柄を含む計算結果が準備される
    Act
    - 現在と調整後のサマリーが生成される
    Assert
    - 両方が入出金額の絶対値降順かつ同額時は設定順で出力されること
    """
    # Arrange
    current_calculations = (
        _make_calc(name="株式"),
        _make_calc(name="債券"),
        _make_calc(name="金"),
        _make_calc(name="現金"),
    )
    adjusted_calculations = (
        _make_calc(name="株式", flow_amount=Decimal("0")),
        _make_calc(name="債券", flow_amount=Decimal("5000")),
        _make_calc(name="金", flow_amount=Decimal("10000")),
        _make_calc(name="現金", flow_amount=Decimal("5000")),
    )
    config = Config(
        adjustment_amount=Decimal("20000"),
        assets=tuple(calc.asset for calc in current_calculations),
        calculated_assets=current_calculations,
    )
    adj_result = AssetAdjustmentResult(
        assets=tuple(calc.asset for calc in adjusted_calculations),
        calculated_assets=adjusted_calculations,
        adjustment_amount=Decimal("20000"),
    )

    # Act
    current_summary = formatter.format_current_summary(config, adj_result)
    adjusted_summary = formatter.format_adjusted_summary(adj_result)

    # Assert
    expected_order = ("金", "債券", "現金", "株式")
    assert tuple(sorted(expected_order, key=current_summary.index)) == expected_order
    assert tuple(sorted(expected_order, key=adjusted_summary.index)) == expected_order


def test_adjusted_summary_generated_correctly(
    formatter: AssetFormatter,
) -> None:
    """調整後のサマリーが生成されること

    Arrange
    - AssetAdjustmentResultを準備
    Act
    - format_adjusted_summaryを実行
    Assert
    - サマリーに調整後のタイトルが含まれること
    """
    # Arrange
    stock_calc = _make_calc(flow_amount=Decimal("6000"))
    bond_calc = _make_calc(name="債券", flow_amount=Decimal("4000"))
    adj_result = AssetAdjustmentResult(
        assets=(stock_calc.asset, bond_calc.asset),
        calculated_assets=(stock_calc, bond_calc),
        adjustment_amount=Decimal("10000"),
    )

    # Act
    result = formatter.format_adjusted_summary(adj_result)

    # Assert
    assert "追加入金後の資産配分" in result
    assert "株式" in result
    assert "債券" in result
