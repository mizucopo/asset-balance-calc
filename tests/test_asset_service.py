"""資産調整ロジックモジュールのテスト"""

from decimal import Decimal
from typing import Any

import pytest

from src.models.asset import Asset
from src.models.asset_calculation import AssetCalculation
from src.models.config import Config
from src.services.asset_service import AssetService
from tests.conftest import create_config


def test_deposit_distributed_by_target_ratio(
    service: AssetService,
    sample_config: Config,
) -> None:
    """入金額がwater-fillingで各資産に配分されること

    Arrange
    - 入金額100,000円のデータを準備
    Act
    - adjust_assetsを実行
    Assert
    - 各資産への配分額が正の値であること
    - 入金額の合計がadjustment_amountと一致すること（最大余剰法）
    """
    # Arrange
    # Act
    result = service.adjust_assets(sample_config)

    # Assert
    # 各資産への配分額が正の値であること
    assert result.calculated_assets[0].flow_amount >= Decimal("0")
    assert result.calculated_assets[1].flow_amount >= Decimal("0")
    # 入金額の合計がadjustment_amountと一致すること（最大余剰法）
    total_flow = (
        result.calculated_assets[0].flow_amount
        + result.calculated_assets[1].flow_amount
    )
    assert total_flow == Decimal("100000")


def test_withdrawal_distributed_by_target_ratio(
    service: AssetService,
    sample_assets: tuple[Asset, ...],
) -> None:
    """出金額がwater-fillingで各資産から減額されること

    Arrange
    - 出金額100,000円のデータを準備
    Act
    - adjust_assetsを実行
    Assert
    - 各資産からの減額額が負の値であること
    - 出金額の合計がadjustment_amountと一致すること（最大余剰法）
    """
    # Arrange
    config = create_config(assets=sample_assets, adjustment_amount=Decimal("-100000"))

    # Act
    result = service.adjust_assets(config)

    # Assert
    # 各資産からの減額額が負の値であること
    assert result.calculated_assets[0].flow_amount <= Decimal("0")
    assert result.calculated_assets[1].flow_amount <= Decimal("0")
    # 出金額の合計がadjustment_amountと一致すること（最大余剰法）
    total_flow = (
        result.calculated_assets[0].flow_amount
        + result.calculated_assets[1].flow_amount
    )
    assert total_flow == Decimal("-100000")


def test_withdrawal_exceeding_total_raises_value_error(
    service: AssetService,
    sample_assets: tuple[Asset, ...],
) -> None:
    """出金額が総資産額を超える場合はValueErrorが送出されること

    Arrange
    - 出金額が総資産額を超えるConfigを準備
    Act
    - adjust_assetsを実行
    Assert
    - ValueErrorが送出されること
    """
    # Arrange
    config = create_config(
        assets=sample_assets, adjustment_amount=Decimal("-200000000")
    )

    # Act & Assert
    with pytest.raises(ValueError, match="final total would be negative"):
        service.adjust_assets(config)


def test_current_rate_calculated_correctly(
    service: AssetService,
    sample_assets: tuple[Asset, ...],
) -> None:
    """現在配分比率が正しく計算されること

    Arrange
    - 既知の資産構成を準備
    Act
    - update_current_rateを実行
    Assert
    - 各資産の現在配分比率が正しく計算されること
    """
    # Arrange
    config = create_config(assets=sample_assets, adjustment_amount=Decimal("0"))

    # Act
    result = service.update_current_rate(config)

    # Assert
    assert result.calculated_assets[0].current_rate == Decimal("0.6")
    assert result.calculated_assets[1].current_rate == Decimal("0.4")


def test_current_rate_zero_when_total_is_zero(
    service: AssetService,
) -> None:
    """資産合計がゼロの場合は現在配分比率がゼロになること

    Arrange
    - 金額がゼロの資産を準備
    Act
    - update_current_rateを実行
    Assert
    - 各資産の現在配分比率がゼロになること
    """
    # Arrange
    assets = (
        Asset(name="株式", amount=Decimal("0"), rate=Decimal("0.60")),
        Asset(name="債券", amount=Decimal("0"), rate=Decimal("0.40")),
    )
    config = create_config(assets=assets, adjustment_amount=Decimal("0"))

    # Act
    result = service.update_current_rate(config)

    # Assert
    assert result.calculated_assets[0].current_rate == Decimal("0")
    assert result.calculated_assets[1].current_rate == Decimal("0")


def test_zero_adjustment_leaves_assets_unchanged(
    service: AssetService,
    sample_assets: tuple[Asset, ...],
) -> None:
    """調整額がゼロの場合は資産が変更されないこと

    Arrange
    - 調整額ゼロのConfigを準備
    Act
    - adjust_assetsを実行
    Assert
    - 資産が変更されないこと
    """
    # Arrange
    config = create_config(assets=sample_assets, adjustment_amount=Decimal("0"))
    original_amounts = tuple(asset.amount for asset in config.assets)

    # Act
    result = service.adjust_assets(config)

    # Assert
    result_amounts = tuple(asset.amount for asset in result.assets)
    assert result_amounts == original_amounts


def test_single_asset_portfolio_deposit_works(
    service: AssetService,
) -> None:
    """単一資産ポートフォリオで入金が正しく動作すること

    Arrange
    - 単一資産のConfigを準備
    Act
    - adjust_assetsを実行
    Assert
    - 全額がその資産に追加されること
    """
    # Arrange
    assets = (Asset(name="株式", amount=Decimal("50000000"), rate=Decimal("1")),)
    calculated_assets = tuple(AssetCalculation(asset=asset) for asset in assets)
    config = Config(
        adjustment_amount=Decimal("10000"),
        assets=assets,
        calculated_assets=calculated_assets,
    )

    # Act
    result = service.adjust_assets(config)

    # Assert
    assert result.calculated_assets[0].flow_amount == Decimal("10000")
    assert result.assets[0].amount == Decimal("50010000")


# テストケースのデータ定義
TEST_CASES_01_07 = [
    # test_case_01: 入金_ちょうど目標に一致するケース
    {
        "id": "test_case_01",
        "name": "入金_ちょうど目標に一致するケース",
        "current": {"stocks": 30000, "bonds": 10000, "reit": 5000, "gold": 5000},
        "target": {"stocks": 0.60, "bonds": 0.20, "reit": 0.10, "gold": 0.10},
        "flow": 0,
        "expected_delta": {"stocks": 0, "bonds": 0, "reit": 0, "gold": 0},
        "expected_final": {"stocks": 30000, "bonds": 10000, "reit": 5000, "gold": 5000},
        "expected_error": None,
    },
    # test_case_02: 入金_不足額をそのまま埋めれば完全一致するケース
    {
        "id": "test_case_02",
        "name": "入金_不足額をそのまま埋めれば完全一致するケース",
        "current": {"stocks": 20000, "bonds": 5000, "reit": 5000, "gold": 0},
        "target": {"stocks": 0.50, "bonds": 0.20, "reit": 0.20, "gold": 0.10},
        "flow": 20000,
        "expected_delta": {"stocks": 5000, "bonds": 5000, "reit": 5000, "gold": 5000},
        "expected_final": {
            "stocks": 25000,
            "bonds": 10000,
            "reit": 10000,
            "gold": 5000,
        },
        "expected_error": None,
    },
    # test_case_03: 入金_不足額比例配分_端数切り捨てあり
    {
        "id": "test_case_03",
        "name": "入金_不足額比例配分_端数切り捨てあり",
        "current": {"stocks": 10000, "bonds": 10000, "reit": 10000, "gold": 10000},
        "target": {"stocks": 0.70, "bonds": 0.20, "reit": 0.05, "gold": 0.05},
        "flow": 10000,
        "expected_delta": {"stocks": 10000, "bonds": 0, "reit": 0, "gold": 0},
        "expected_final": {
            "stocks": 20000,
            "bonds": 10000,
            "reit": 10000,
            "gold": 10000,
        },
        "expected_error": None,
    },
    # test_case_04: 入金_複数資産water-filling_最大余剰法あり
    {
        "id": "test_case_04",
        "name": "入金_複数資産water-filling_最大余剰法あり",
        "current": {"stocks": 10000, "bonds": 10000, "reit": 10000, "gold": 10000},
        "target": {"stocks": 0.50, "bonds": 0.30, "reit": 0.15, "gold": 0.05},
        "flow": 10001,
        "expected_delta": {"stocks": 8751, "bonds": 1250, "reit": 0, "gold": 0},
        "expected_final": {
            "stocks": 18751,
            "bonds": 11250,
            "reit": 10000,
            "gold": 10000,
        },
        "expected_error": None,
    },
    # test_case_05: 出金_ちょうど目標に一致するケース
    {
        "id": "test_case_05",
        "name": "出金_ちょうど目標に一致するケース",
        "current": {"stocks": 40000, "bonds": 20000, "reit": 10000, "gold": 10000},
        "target": {"stocks": 0.60, "bonds": 0.20, "reit": 0.10, "gold": 0.10},
        "flow": -30000,
        "expected_delta": {
            "stocks": -10000,
            "bonds": -10000,
            "reit": -5000,
            "gold": -5000,
        },
        "expected_final": {"stocks": 30000, "bonds": 10000, "reit": 5000, "gold": 5000},
        "expected_error": None,
    },
    # test_case_06: 出金_最も水位の高いアセットから優先引出
    {
        "id": "test_case_06",
        "name": "出金_最も水位の高いアセットから優先引出",
        "current": {"stocks": 50000, "bonds": 10000, "reit": 10000, "gold": 10000},
        "target": {"stocks": 0.40, "bonds": 0.30, "reit": 0.20, "gold": 0.10},
        "flow": -10000,
        "expected_delta": {"stocks": -10000, "bonds": 0, "reit": 0, "gold": 0},
        "expected_final": {
            "stocks": 40000,
            "bonds": 10000,
            "reit": 10000,
            "gold": 10000,
        },
        "expected_error": None,
    },
    # test_case_07: 出金_複数超過アセットのwater-filling_最大余剰法あり
    {
        "id": "test_case_07",
        "name": "出金_複数超過アセットのwater-filling_最大余剰法あり",
        "current": {"stocks": 30000, "bonds": 30000, "reit": 30000, "gold": 10000},
        "target": {"stocks": 0.50, "bonds": 0.20, "reit": 0.20, "gold": 0.10},
        "flow": -10001,
        "expected_delta": {"stocks": 0, "bonds": -5001, "reit": -5000, "gold": 0},
        "expected_final": {
            "stocks": 30000,
            "bonds": 24999,
            "reit": 25000,
            "gold": 10000,
        },
        "expected_error": None,
    },
]


TEST_CASES_08_12 = [
    # test_case_08: 入金_最も水位の低いアセットに全額配分
    {
        "id": "test_case_08",
        "name": "入金_最も水位の低いアセットに全額配分",
        "current": {"stocks": 10000, "bonds": 50000, "reit": 10000, "gold": 10000},
        "target": {"stocks": 0.50, "bonds": 0.20, "reit": 0.20, "gold": 0.10},
        "flow": 10000,
        "expected_delta": {"stocks": 10000, "bonds": 0, "reit": 0, "gold": 0},
        "expected_final": {
            "stocks": 20000,
            "bonds": 50000,
            "reit": 10000,
            "gold": 10000,
        },
        "expected_error": None,
    },
    # test_case_09: 出金_超過アセット2つのwater-filling
    {
        "id": "test_case_09",
        "name": "出金_超過アセット2つのwater-filling",
        "current": {"stocks": 10000, "bonds": 10000, "reit": 50000, "gold": 30000},
        "target": {"stocks": 0.40, "bonds": 0.30, "reit": 0.20, "gold": 0.10},
        "flow": -20000,
        "expected_delta": {"stocks": 0, "bonds": 0, "reit": -10000, "gold": -10000},
        "expected_final": {
            "stocks": 10000,
            "bonds": 10000,
            "reit": 40000,
            "gold": 20000,
        },
        "expected_error": None,
    },
    # test_case_10: 2資産_入金
    {
        "id": "test_case_10",
        "name": "2資産_入金",
        "current": {"risky": 10000, "safe": 30000},
        "target": {"risky": 0.50, "safe": 0.50},
        "flow": 10000,
        "expected_delta": {"risky": 10000, "safe": 0},
        "expected_final": {"risky": 20000, "safe": 30000},
        "expected_error": None,
    },
    # test_case_11: 2資産_出金
    {
        "id": "test_case_11",
        "name": "2資産_出金",
        "current": {"risky": 40000, "safe": 10000},
        "target": {"risky": 0.50, "safe": 0.50},
        "flow": -10000,
        "expected_delta": {"risky": -10000, "safe": 0},
        "expected_final": {"risky": 30000, "safe": 10000},
        "expected_error": None,
    },
    # test_case_12: 全額出金（final_total=0）はValueError
    # 理由: 全アセットの flow_amount を 0 にするだけなら
    # flow=0 で表現可能。資産額を0にする操作は別途検討すべき
    {
        "id": "test_case_12",
        "name": "境界値_全額出金はValueError",
        "current": {"stocks": 15000, "bonds": 10000, "reit": 5000, "gold": 20000},
        "target": {"stocks": 0.40, "bonds": 0.30, "reit": 0.20, "gold": 0.10},
        "flow": -50000,
        "expected_delta": None,
        "expected_final": None,
        "expected_error": "final total would be negative",
    },
]


TEST_CASES_13 = [
    # test_case_13: 異常系_最終総額が負
    {
        "id": "test_case_13",
        "name": "異常系_最終総額が負",
        "current": {"stocks": 10000, "bonds": 10000, "reit": 10000, "gold": 10000},
        "target": {"stocks": 0.25, "bonds": 0.25, "reit": 0.25, "gold": 0.25},
        "flow": -50000,
        "expected_delta": None,
        "expected_final": None,
        "expected_error": "final total would be negative",
    },
]


def _build_config_from_case(case: dict[str, Any]) -> Config:
    """テストケースからConfigを構築するヘルパー関数

    Args:
        case: テストケースデータ

    Returns:
        構築されたConfig
    """
    assets = tuple(
        Asset(
            name=name,
            amount=Decimal(str(amount)),
            rate=Decimal(str(case["target"][name])),
        )
        for name, amount in case["current"].items()
    )
    return create_config(assets=assets, adjustment_amount=Decimal(str(case["flow"])))


def _get_delta(calc: AssetCalculation) -> Decimal:
    """AssetCalculationからdelta（増減額）を取得する

    Args:
        calc: 計算結果

    Returns:
        増減額（出金時は負の値）
    """
    return calc.flow_amount


_IDS_01_07 = [str(c["id"]) for c in TEST_CASES_01_07]


@pytest.mark.parametrize("case", TEST_CASES_01_07, ids=_IDS_01_07)
def test_water_filling_allocation_cases_01_07(
    service: AssetService,
    case: dict[str, Any],
) -> None:
    """water-filling配分ロジックが正しく動作すること（テストケース01-07）

    Arrange
    - テストケースのデータからConfigを構築
    Act
    - adjust_assetsを実行
    Assert
    - 各資産のdeltaとfinalが期待値と一致すること
    """
    # Arrange
    config = _build_config_from_case(case)

    # Act
    result = service.adjust_assets(config)

    # Assert
    for calc in result.calculated_assets:
        name = calc.asset.name
        delta = _get_delta(calc)
        expected_delta = Decimal(str(case["expected_delta"][name]))
        expected_final = Decimal(str(case["expected_final"][name]))

        assert delta == expected_delta, (
            f"{name}: delta {delta} != expected {expected_delta}"
        )
        assert calc.asset.amount == expected_final, (
            f"{name}: final {calc.asset.amount} != expected {expected_final}"
        )


_IDS_08_12 = [str(c["id"]) for c in TEST_CASES_08_12]


@pytest.mark.parametrize("case", TEST_CASES_08_12, ids=_IDS_08_12)
def test_water_filling_allocation_cases_08_12(
    service: AssetService,
    case: dict[str, Any],
) -> None:
    """water-filling配分ロジックが正しく動作すること（テストケース08-12）

    Arrange
    - テストケースのデータからConfigを構築
    Act
    - adjust_assetsを実行
    Assert
    - 各資産のdeltaとfinalが期待値と一致すること
    - エラー期待値がある場合はValueErrorが送出されること
    """
    # Arrange
    config = _build_config_from_case(case)

    # Act & Assert
    if case["expected_error"]:
        with pytest.raises(ValueError, match=str(case["expected_error"])):
            service.adjust_assets(config)
        return

    result = service.adjust_assets(config)

    for calc in result.calculated_assets:
        name = calc.asset.name
        delta = _get_delta(calc)
        expected_delta = Decimal(str(case["expected_delta"][name]))
        expected_final = Decimal(str(case["expected_final"][name]))

        assert delta == expected_delta, (
            f"{name}: delta {delta} != expected {expected_delta}"
        )
        assert calc.asset.amount == expected_final, (
            f"{name}: final {calc.asset.amount} != expected {expected_final}"
        )


def test_water_filling_allocation_case_13_error(service: AssetService) -> None:
    """異常系：最終総額が負になる場合はエラーが発生すること

    Arrange
    - 出金額が総資産を超えるConfigを準備
    Act & Assert
    - ValueErrorが送出されること
    """
    # Arrange
    case = TEST_CASES_13[0]  # test_case_13
    config = _build_config_from_case(case)

    # Act & Assert
    with pytest.raises(ValueError, match=str(case["expected_error"])):
        service.adjust_assets(config)


def test_deposit_waterfilling_two_underweight_assets(
    service: AssetService,
) -> None:
    """入金時のwater-fillingで水位の低いアセットが優先されること

    Arrange
    - 2つの不足アセットと2つの超過アセットを準備
    Act
    - adjust_assetsを実行
    Assert
    - 最も水位の低いアセットに多く配分されること
    - flow_amountの合計がflowと一致すること
    """
    # Arrange
    assets = (
        Asset(name="stocks", amount=Decimal("10000"), rate=Decimal("0.50")),
        Asset(name="bonds", amount=Decimal("10000"), rate=Decimal("0.30")),
        Asset(name="reit", amount=Decimal("10000"), rate=Decimal("0.15")),
        Asset(name="gold", amount=Decimal("10000"), rate=Decimal("0.05")),
    )
    config = create_config(assets=assets, adjustment_amount=Decimal("10001"))

    # Act
    result = service.adjust_assets(config)

    # Assert
    # stocks level=20000, bonds level=33333.33, reit level=66666.66,
    # gold level=200000
    # final_total=50001, 不足: stocks, bonds
    # Step1: stocksをbondsまで引き上げ cost=6666.67
    # Step2: 両方を引き上げ remaining=3334.33 / 0.80 = 4167.92
    # stocks exact=8750.625, bonds exact=1250.375
    # 最大余剰法: stocks=8751, bonds=1250
    flow_map = {calc.asset.name: calc.flow_amount for calc in result.calculated_assets}
    assert flow_map["stocks"] == Decimal("8751")
    assert flow_map["bonds"] == Decimal("1250")
    assert flow_map["reit"] == Decimal("0")
    assert flow_map["gold"] == Decimal("0")
    # 合計がflowと一致
    total = sum(calc.flow_amount for calc in result.calculated_assets)
    assert total == Decimal("10001")


def test_withdrawal_waterfilling_two_overweight_assets(
    service: AssetService,
) -> None:
    """出金時のwater-fillingで水位の高いアセットが優先されること

    Arrange
    - 2つの超過アセットと2つの不足アセットを準備
    Act
    - adjust_assetsを実行
    Assert
    - 最も水位の高いアセットから多く引出されること
    - flow_amountの合計がflowと一致すること
    """
    # Arrange
    assets = (
        Asset(name="stocks", amount=Decimal("10000"), rate=Decimal("0.40")),
        Asset(name="bonds", amount=Decimal("10000"), rate=Decimal("0.30")),
        Asset(name="reit", amount=Decimal("50000"), rate=Decimal("0.20")),
        Asset(name="gold", amount=Decimal("30000"), rate=Decimal("0.10")),
    )
    config = create_config(assets=assets, adjustment_amount=Decimal("-20000"))

    # Act
    result = service.adjust_assets(config)

    # Assert
    # stocks level=25000, bonds level=33333.33, reit level=250000,
    # gold level=300000
    # final_total=80000, 超過: reit(250000), gold(300000)
    # Step1: gold(300000)をreit(250000)まで引き下げ cost=5000
    # Step2: 両方を引き下げ remaining=15000 / 0.30 = 50000
    # gold exact=-10000, reit exact=-10000
    # 端数なし（整数）
    flow_map = {calc.asset.name: calc.flow_amount for calc in result.calculated_assets}
    assert flow_map["gold"] == Decimal("-10000")
    assert flow_map["reit"] == Decimal("-10000")
    assert flow_map["stocks"] == Decimal("0")
    assert flow_map["bonds"] == Decimal("0")
    # 合計がflowと一致
    total = sum(calc.flow_amount for calc in result.calculated_assets)
    assert total == Decimal("-20000")


def test_zero_flow_returns_all_zero(
    service: AssetService,
    sample_assets: tuple[Asset, ...],
) -> None:
    """flow=0の場合は全アセットのflow_amountが0であること

    Arrange
    - 調整額ゼロのConfigを準備
    Act
    - adjust_assetsを実行
    Assert
    - 全アセットのflow_amountが0であること
    """
    # Arrange
    config = create_config(assets=sample_assets, adjustment_amount=Decimal("0"))

    # Act
    result = service.adjust_assets(config)

    # Assert
    for calc in result.calculated_assets:
        assert calc.flow_amount == Decimal("0")


def test_final_total_zero_raises_value_error(
    service: AssetService,
) -> None:
    """final_totalが0になる場合はValueErrorが送出されること

    Arrange
    - 総資産と同額の出金を準備
    Act & Assert
    - ValueErrorが送出されること
    """
    # Arrange
    assets = (
        Asset(name="stocks", amount=Decimal("30000"), rate=Decimal("0.60")),
        Asset(name="bonds", amount=Decimal("20000"), rate=Decimal("0.40")),
    )
    config = create_config(assets=assets, adjustment_amount=Decimal("-50000"))

    # Act & Assert
    with pytest.raises(ValueError, match="final total would be negative"):
        service.adjust_assets(config)


def test_final_total_negative_raises_value_error(
    service: AssetService,
) -> None:
    """final_totalが負になる場合はValueErrorが送出されること

    Arrange
    - 総資産を超える出金を準備
    Act & Assert
    - ValueErrorが送出されること
    """
    # Arrange
    assets = (
        Asset(name="stocks", amount=Decimal("30000"), rate=Decimal("0.60")),
        Asset(name="bonds", amount=Decimal("20000"), rate=Decimal("0.40")),
    )
    config = create_config(assets=assets, adjustment_amount=Decimal("-60000"))

    # Act & Assert
    with pytest.raises(ValueError, match="final total would be negative"):
        service.adjust_assets(config)


def test_all_assets_at_target_deposit_distributes_proportionally(
    service: AssetService,
) -> None:
    """全アセットが目標どおりのとき入金がrate比例配分されること

    Arrange
    - 全アセットが目標比率どおりのConfigを準備
    Act
    - adjust_assetsを実行
    Assert
    - 各アセットにrate比例で配分されること
    - flow_amountの合計がflowと一致すること
    """
    # Arrange
    assets = (
        Asset(name="stocks", amount=Decimal("30000"), rate=Decimal("0.50")),
        Asset(name="bonds", amount=Decimal("18000"), rate=Decimal("0.30")),
        Asset(name="reit", amount=Decimal("12000"), rate=Decimal("0.20")),
    )
    config = create_config(assets=assets, adjustment_amount=Decimal("10000"))

    # Act
    result = service.adjust_assets(config)

    # Assert
    # 全レベル = current_total = 60000, 全不足 → 全員同時に引き上げ
    # → rate比例
    # 各アセット flow = 10000 * rate
    flow_map = {calc.asset.name: calc.flow_amount for calc in result.calculated_assets}
    assert flow_map["stocks"] == Decimal("5000")
    assert flow_map["bonds"] == Decimal("3000")
    assert flow_map["reit"] == Decimal("2000")
    total = sum(calc.flow_amount for calc in result.calculated_assets)
    assert total == Decimal("10000")


def test_adjust_assets_without_calculated_assets_raises_value_error(
    service: AssetService,
) -> None:
    """calculated_assetsが未設定のConfigでadjust_assetsを実行するとValueErrorが送出されること

    Arrange
    - calculated_assetsが空のConfigを準備
    Act & Assert
    - ValueErrorが送出されること
    """
    # Arrange
    assets = (
        Asset(name="株式", amount=Decimal("60000000"), rate=Decimal("0.60")),
        Asset(name="債券", amount=Decimal("40000000"), rate=Decimal("0.40")),
    )
    config = Config(
        adjustment_amount=Decimal("100000"),
        assets=assets,
    )

    # Act & Assert
    with pytest.raises(ValueError, match="calculated_assets"):
        service.adjust_assets(config)


def test_adjust_assets_without_calculated_assets_zero_flow_ok(
    service: AssetService,
) -> None:
    """calculated_assetsが未設定でもadjustment_amount=0の場合はエラーにならないこと

    Arrange
    - calculated_assetsが空でadjustment_amount=0のConfigを準備
    Act
    - adjust_assetsを実行
    Assert
    - Configがそのまま返されること
    """
    # Arrange
    assets = (
        Asset(name="株式", amount=Decimal("60000000"), rate=Decimal("0.60")),
        Asset(name="債券", amount=Decimal("40000000"), rate=Decimal("0.40")),
    )
    config = Config(
        adjustment_amount=Decimal("0"),
        assets=assets,
    )

    # Act
    result = service.adjust_assets(config)

    # Assert
    assert result.assets == config.assets
