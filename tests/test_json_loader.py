"""JSON読み込みモジュールのテスト"""

from decimal import Decimal
from pathlib import Path

import pytest

from src.json_loader import JsonLoader
from src.models.asset_raw import AssetRaw
from src.models.config_raw import ConfigRaw


def test_config_raw_converted_to_config_correctly(
    loader: JsonLoader,
) -> None:
    """ConfigRawがConfigに正しく変換されること

    Arrange
    - ConfigRawデータを準備
    Act
    - convert_to_configを実行
    Assert
    - 各値が正しくDecimalに変換されること
    """
    # Arrange
    raw_data = ConfigRaw(
        adjustment_amount="80,000",
        assets=(
            AssetRaw(name="株式", amount="60,000,000", rate="0.60"),
            AssetRaw(name="債券", amount="40,000,000", rate="0.40"),
        ),
    )

    # Act
    result = loader.convert_to_config(raw_data)

    # Assert
    assert result.adjustment_amount == Decimal("80000")
    assert result.assets[0].amount == Decimal("60000000")
    assert result.assets[0].rate == Decimal("0.60")


def test_json_file_loaded_and_converted_to_decimal(
    loader: JsonLoader,
    tmp_path: Path,
) -> None:
    """設定ファイルが正しく読み込まれDecimalに変換されること

    Arrange
    - テスト用JSONファイルを作成
    Act
    - load_jsonを実行
    Assert
    - 各値がDecimalに変換されること
    """
    # Arrange
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"adjustment_amount": "80,000", '
        '"assets": [{"name": "株式", "amount": "60,000,000", "rate": "0.60"}, '
        '{"name": "債券", "amount": "40,000,000", "rate": "0.40"}]}',
        encoding="utf-8",
    )

    # Act
    result = loader.load_json(str(config_file))

    # Assert
    # adjustment_amountが正しく変換されること
    assert result.adjustment_amount == Decimal("80000")
    # assetsの値がDecimalに変換されること
    assert result.assets[0].amount == Decimal("60000000")
    assert result.assets[0].rate == Decimal("0.60")
    # calculated_assetsは初期状態では空であること
    assert result.calculated_assets == ()


def test_rate_sum_not_equal_to_one_raises_value_error(
    loader: JsonLoader,
) -> None:
    """目標配分割合の合計が1でない場合はValueErrorが送出されること

    Arrange
    - rateの合計が1.0でないConfigRawデータを準備
    Act
    - convert_to_configを実行
    Assert
    - ValueErrorが送出されること
    """
    # Arrange
    raw_data = ConfigRaw(
        adjustment_amount="80,000",
        assets=(
            AssetRaw(name="株式", amount="60,000,000", rate="0.50"),
            AssetRaw(name="債券", amount="40,000,000", rate="0.30"),
        ),
    )

    # Act & Assert
    with pytest.raises(ValueError, match="目標配分割合の合計が1.0ではありません"):
        loader.convert_to_config(raw_data)


def test_rate_zero_raises_value_error(
    loader: JsonLoader,
) -> None:
    """目標配分割合に0が含まれる場合はValueErrorが送出されること

    Arrange
    - rateに0を含むConfigRawデータを準備
    Act & Assert
    - ValueErrorが送出されること
    """
    # Arrange
    raw_data = ConfigRaw(
        adjustment_amount="10,000",
        assets=(
            AssetRaw(name="株式", amount="60,000,000", rate="1.00"),
            AssetRaw(name="債券", amount="40,000,000", rate="0.00"),
        ),
    )

    # Act & Assert
    with pytest.raises(ValueError, match="目標配分割合は正の値である必要があります"):
        loader.convert_to_config(raw_data)


def test_rate_negative_raises_value_error(
    loader: JsonLoader,
) -> None:
    """目標配分割合に負の値が含まれる場合はValueErrorが送出されること

    Arrange
    - rateに負の値を含むConfigRawデータを準備
    Act & Assert
    - ValueErrorが送出されること
    """
    # Arrange
    raw_data = ConfigRaw(
        adjustment_amount="10,000",
        assets=(
            AssetRaw(name="株式", amount="60,000,000", rate="1.20"),
            AssetRaw(name="債券", amount="40,000,000", rate="-0.20"),
        ),
    )

    # Act & Assert
    with pytest.raises(ValueError, match="目標配分割合は正の値である必要があります"):
        loader.convert_to_config(raw_data)


def test_amount_non_integer_raises_value_error(
    loader: JsonLoader,
) -> None:
    """金額が整数でない場合はValueErrorが送出されること

    Arrange
    - amountに小数を含むConfigRawデータを準備
    Act & Assert
    - ValueErrorが送出されること
    """
    # Arrange
    raw_data = ConfigRaw(
        adjustment_amount="10,000",
        assets=(
            AssetRaw(name="株式", amount="60,000,000.5", rate="0.60"),
            AssetRaw(name="債券", amount="40,000,000", rate="0.40"),
        ),
    )

    # Act & Assert
    with pytest.raises(ValueError, match="金額は整数である必要があります"):
        loader.convert_to_config(raw_data)


def test_adjustment_amount_non_integer_raises_value_error(
    loader: JsonLoader,
) -> None:
    """調整額が整数でない場合はValueErrorが送出されること

    Arrange
    - adjustment_amountに小数を含むConfigRawデータを準備
    Act & Assert
    - ValueErrorが送出されること
    """
    # Arrange
    raw_data = ConfigRaw(
        adjustment_amount="10,000.5",
        assets=(
            AssetRaw(name="株式", amount="60,000,000", rate="0.60"),
            AssetRaw(name="債券", amount="40,000,000", rate="0.40"),
        ),
    )

    # Act & Assert
    with pytest.raises(ValueError, match="金額は整数である必要があります"):
        loader.convert_to_config(raw_data)


def test_amount_negative_raises_value_error(
    loader: JsonLoader,
) -> None:
    """金額が負の値の場合はValueErrorが送出されること

    Arrange
    - amountに負の値を含むConfigRawデータを準備
    Act & Assert
    - ValueErrorが送出されること
    """
    # Arrange
    raw_data = ConfigRaw(
        adjustment_amount="10,000",
        assets=(
            AssetRaw(name="株式", amount="-1,000", rate="0.60"),
            AssetRaw(name="債券", amount="40,000,000", rate="0.40"),
        ),
    )

    # Act & Assert
    with pytest.raises(ValueError, match="金額は正の値である必要があります"):
        loader.convert_to_config(raw_data)
