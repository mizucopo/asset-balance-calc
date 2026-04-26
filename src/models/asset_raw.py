"""JSONからの入力用AssetRawデータクラス"""

from dataclasses import dataclass


@dataclass(frozen=True)
class AssetRaw:
    """JSONから読み込む資産データ

    Attributes:
        name: 資産名
        amount: 金額（カンマ区切り文字列）
        rate: 目標配分割合
    """

    name: str
    amount: str
    rate: str
