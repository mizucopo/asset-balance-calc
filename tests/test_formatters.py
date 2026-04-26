"""フォーマット処理モジュールのテスト"""

from decimal import Decimal

from src.formatters import AssetFormatter
from src.models.asset import Asset
from src.models.asset_calculation import AssetCalculation
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

    # Act
    result = formatter.format_current_summary(config)

    # Assert
    assert "現在の資産配分" in result
    assert "株式" in result
    assert "債券" in result


def test_adjusted_summary_generated_correctly(
    formatter: AssetFormatter,
) -> None:
    """調整後のサマリーが生成されること

    Arrange
    - calculated_assetsを持つConfigを準備
    Act
    - format_adjusted_summaryを実行
    Assert
    - サマリーに調整後のタイトルが含まれること
    """
    # Arrange
    bond_calc = _make_calc(name="債券", flow_amount=Decimal("4000"))
    config = Config(
        adjustment_amount=Decimal("10000"),
        assets=(),
        calculated_assets=(_make_calc(flow_amount=Decimal("6000")), bond_calc),
    )

    # Act
    result = formatter.format_adjusted_summary(config)

    # Assert
    assert "追加入金後の資産配分" in result
    assert "株式" in result
    assert "債券" in result
