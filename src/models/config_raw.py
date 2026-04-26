"""JSONからの入力用ConfigRawデータクラス"""

from dataclasses import dataclass

from src.models.asset_raw import AssetRaw


@dataclass(frozen=True)
class ConfigRaw:
    """JSONから読み込む設定データ

    Attributes:
        adjustment_amount: 調整額（正: 入金、負: 出金、カンマ区切り文字列）
        assets: 資産リスト
    """

    adjustment_amount: str
    assets: tuple[AssetRaw, ...]
