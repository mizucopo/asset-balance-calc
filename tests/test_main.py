"""CLIエントリーポイントとAssetService統合テスト"""

from decimal import Decimal
from typing import Any

import pytest
from click.testing import CliRunner
from mizu_common import Asset, AssetService

from src.main import main

# --- CLI テスト ---


def test_runs_with_default_config_path() -> None:
    """デフォルトの設定ファイルパスで実行されること

    Arrange
    - CliRunnerを準備
    Act
    - オプションなしでmainを実行
    Assert
    - 終了コードが0であること
    """
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(main)

    # Assert
    assert result.exit_code == 0


def test_custom_config_path_loaded() -> None:
    """カスタム設定ファイルパスが指定された場合に読み込まれること

    Arrange
    - CliRunnerとオプション引数を準備
    Act
    - -cオプションで設定ファイルを指定してmainを実行
    Assert
    - 終了コードが0であること
    """
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(main, ["-c", "./config/config.json"])

    # Assert
    assert result.exit_code == 0


def test_nonexistent_config_file_raises_error() -> None:
    """存在しない設定ファイルを指定した場合にエラーになること

    Arrange
    - CliRunnerと存在しないファイルパスを準備
    Act
    - 存在しないファイルを指定してmainを実行
    Assert
    - 終了コードが0以外であること
    """
    # Arrange
    runner = CliRunner()

    # Act
    result = runner.invoke(main, ["-c", "./config/not_exist.json"])

    # Assert
    assert result.exit_code != 0


# --- 統合テスト: mizu_common AssetService 経由 ---


def _make_assets(**amounts: int) -> tuple[Asset, ...]:
    """テスト用Assetタプルを生成すること"""
    rates = {
        "stocks": Decimal("0.60"),
        "bonds": Decimal("0.40"),
    }
    assets_list = []
    rate_total = Decimal("0")
    names = list(amounts.keys())
    for i, name in enumerate(names):
        if i < len(names) - 1:
            rate = rates.get(name, Decimal("0.25"))
        else:
            rate = Decimal("1") - rate_total
        rate_total += rate
        assets_list.append(
            Asset(name=name, amount=Decimal(str(amounts[name])), rate=rate)
        )
    return tuple(assets_list)


def test_deposit_distributed_by_target_ratio() -> None:
    """入金額がwater-fillingで各資産に配分されること

    Arrange
    - 入金額100,000円のデータを準備
    Act
    - calculate_current_rates → adjust_assetsを実行
    Assert
    - 入金額の合計がadjustment_amountと一致すること
    """
    # Arrange
    service = AssetService()
    assets = (
        Asset(name="株式", amount=Decimal("60000000"), rate=Decimal("0.60")),
        Asset(name="債券", amount=Decimal("40000000"), rate=Decimal("0.40")),
    )

    # Act
    calculated = service.calculate_current_rates(assets)
    result = service.adjust_assets(calculated, Decimal("100000"))

    # Assert
    total_flow = sum(calc.flow_amount for calc in result.calculated_assets)
    assert total_flow == Decimal("100000")


def test_withdrawal_distributed_by_target_ratio() -> None:
    """出金額がwater-fillingで各資産から減額されること

    Arrange
    - 出金額100,000円のデータを準備
    Act
    - calculate_current_rates → adjust_assetsを実行
    Assert
    - 出金額の合計がadjustment_amountと一致すること
    """
    # Arrange
    service = AssetService()
    assets = (
        Asset(name="株式", amount=Decimal("60000000"), rate=Decimal("0.60")),
        Asset(name="債券", amount=Decimal("40000000"), rate=Decimal("0.40")),
    )

    # Act
    calculated = service.calculate_current_rates(assets)
    result = service.adjust_assets(calculated, Decimal("-100000"))

    # Assert
    total_flow = sum(calc.flow_amount for calc in result.calculated_assets)
    assert total_flow == Decimal("-100000")


def test_current_rate_calculated_correctly() -> None:
    """現在配分比率が正しく計算されること

    Arrange
    - 既知の資産構成を準備
    Act
    - calculate_current_ratesを実行
    Assert
    - 各資産の現在配分比率が正しく計算されること
    """
    # Arrange
    service = AssetService()
    assets = (
        Asset(name="株式", amount=Decimal("60000000"), rate=Decimal("0.60")),
        Asset(name="債券", amount=Decimal("40000000"), rate=Decimal("0.40")),
    )

    # Act
    result = service.calculate_current_rates(assets)

    # Assert
    assert result[0].current_rate == Decimal("0.6")
    assert result[1].current_rate == Decimal("0.4")


def test_zero_adjustment_leaves_assets_unchanged() -> None:
    """調整額がゼロの場合は資産が変更されないこと

    Arrange
    - 調整額ゼロのデータを準備
    Act
    - calculate_current_rates → adjust_assetsを実行
    Assert
    - 資産が変更されないこと
    """
    # Arrange
    service = AssetService()
    assets = (
        Asset(name="株式", amount=Decimal("60000000"), rate=Decimal("0.60")),
        Asset(name="債券", amount=Decimal("40000000"), rate=Decimal("0.40")),
    )

    # Act
    calculated = service.calculate_current_rates(assets)
    result = service.adjust_assets(calculated, Decimal("0"))

    # Assert
    original_amounts = tuple(asset.amount for asset in assets)
    result_amounts = tuple(asset.amount for asset in result.assets)
    assert result_amounts == original_amounts


def test_zero_total_amount_raises_value_error() -> None:
    """資産合計がゼロの場合はValueErrorが送出されること

    Arrange
    - 金額がゼロの資産を準備
    Act & Assert
    - ValueErrorが送出されること
    """
    # Arrange
    service = AssetService()
    assets = (
        Asset(name="株式", amount=Decimal("0"), rate=Decimal("0.60")),
        Asset(name="債券", amount=Decimal("0"), rate=Decimal("0.40")),
    )

    # Act & Assert
    with pytest.raises(ValueError, match="total amount must be positive"):
        service.calculate_current_rates(assets)


# --- 統合テスト: CLI経由で主要 water-filling ケースを検証 ---


def _write_config_json(tmp_path: Any, config_data: str) -> str:
    """テスト用JSONファイルを生成すること"""
    config_file = tmp_path / "config.json"
    config_file.write_text(config_data, encoding="utf-8")
    return str(config_file)


def test_cli_deposit_produces_correct_output(tmp_path: Any) -> None:
    """CLIで入金時の出力が正しいこと

    Arrange
    - 入金設定のJSONファイルを準備
    Act
    - CLIを実行
    Assert
    - 追加入金後の資産配分が出力されること
    """
    # Arrange
    runner = CliRunner()
    config_path = _write_config_json(
        tmp_path,
        '{"adjustment_amount": "100,000", '
        '"assets": [{"name": "株式", "amount": "60,000,000", "rate": "0.60"}, '
        '{"name": "債券", "amount": "40,000,000", "rate": "0.40"}]}',
    )

    # Act
    result = runner.invoke(main, ["-c", config_path])

    # Assert
    assert result.exit_code == 0
    assert "追加入金後の資産配分" in result.output


def test_cli_withdrawal_produces_correct_output(tmp_path: Any) -> None:
    """CLIで出金時の出力が正しいこと

    Arrange
    - 出金設定のJSONファイルを準備
    Act
    - CLIを実行
    Assert
    - 出金後の資産配分が出力されること
    """
    # Arrange
    runner = CliRunner()
    config_path = _write_config_json(
        tmp_path,
        '{"adjustment_amount": "-100,000", '
        '"assets": [{"name": "株式", "amount": "60,000,000", "rate": "0.60"}, '
        '{"name": "債券", "amount": "40,000,000", "rate": "0.40"}]}',
    )

    # Act
    result = runner.invoke(main, ["-c", config_path])

    # Assert
    assert result.exit_code == 0
    assert "出金後の資産配分" in result.output


def test_cli_zero_adjustment_produces_correct_output(tmp_path: Any) -> None:
    """CLIで調整額ゼロ時の出力が正しいこと

    Arrange
    - 調整額ゼロのJSONファイルを準備
    Act
    - CLIを実行
    Assert
    - 資産配分が出力されること
    """
    # Arrange
    runner = CliRunner()
    config_path = _write_config_json(
        tmp_path,
        '{"adjustment_amount": "0", '
        '"assets": [{"name": "株式", "amount": "60,000,000", "rate": "0.60"}, '
        '{"name": "債券", "amount": "40,000,000", "rate": "0.40"}]}',
    )

    # Act
    result = runner.invoke(main, ["-c", config_path])

    # Assert
    assert result.exit_code == 0
    assert "資産配分:" in result.output
