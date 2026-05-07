"""テスト用フィクスチャ"""

from decimal import Decimal

import pytest
from mizu_common import (
    Asset,
    AssetCalculation,
    LoggingConfigurator,
)

from src.formatters import AssetFormatter
from src.json_loader import JsonLoader
from src.models.config import Config


@pytest.fixture(autouse=True)
def _reset_logging() -> None:
    """テスト間でログ初期化状態をリセットすること"""
    LoggingConfigurator.reset()


@pytest.fixture
def sample_assets() -> tuple[Asset, ...]:
    """テスト用の共通資産構成が返されること"""
    return (
        Asset(
            name="株式",
            amount=Decimal("60000000"),
            rate=Decimal("0.60"),
        ),
        Asset(
            name="債券",
            amount=Decimal("40000000"),
            rate=Decimal("0.40"),
        ),
    )


def create_config(
    assets: tuple[Asset, ...],
    adjustment_amount: Decimal,
) -> Config:
    """テスト用Configを生成すること"""
    calculated_assets = tuple(AssetCalculation(asset=asset) for asset in assets)
    return Config(
        adjustment_amount=adjustment_amount,
        assets=assets,
        calculated_assets=calculated_assets,
    )


@pytest.fixture
def sample_config(sample_assets: tuple[Asset, ...]) -> Config:
    """テスト用のサンプルConfigが返されること"""
    return create_config(assets=sample_assets, adjustment_amount=Decimal("100000"))


@pytest.fixture
def loader() -> JsonLoader:
    """JsonLoaderのインスタンスが返されること"""
    return JsonLoader()


@pytest.fixture
def formatter() -> AssetFormatter:
    """AssetFormatterのインスタンスが返されること"""
    return AssetFormatter()
