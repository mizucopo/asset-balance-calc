"""処理用Configデータクラス"""

from dataclasses import dataclass, field
from decimal import Decimal

from mizu_common import Asset, AssetAdjustmentType, AssetCalculation


@dataclass(frozen=True)
class Config:
    """処理用の設定データ

    Attributes:
        adjustment_amount: 調整額（正: 入金、負: 出金）
        assets: 資産リスト
        calculated_assets: 計算結果の資産リスト
    """

    adjustment_amount: Decimal
    assets: tuple[Asset, ...]
    calculated_assets: tuple[AssetCalculation, ...] = field(default=())

    @property
    def operation_type(self) -> AssetAdjustmentType:
        """操作タイプを返す

        Returns:
            入金時はDEPOSIT、出金時はWITHDRAWAL、それ以外はNONE
        """
        if self.adjustment_amount > 0:
            return AssetAdjustmentType.DEPOSIT
        if self.adjustment_amount < 0:
            return AssetAdjustmentType.WITHDRAWAL
        return AssetAdjustmentType.NONE
