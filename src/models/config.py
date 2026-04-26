"""処理用Configデータクラス"""

from dataclasses import dataclass, field
from decimal import Decimal

from src.constants.operation_type import OperationType
from src.models.asset import Asset
from src.models.asset_calculation import AssetCalculation


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
    def operation_type(self) -> OperationType:
        """操作タイプを返す

        Returns:
            入金時はDEPOSIT、出金時はWITHDRAWAL、それ以外はNONE
        """
        if self.adjustment_amount > 0:
            return OperationType.DEPOSIT
        if self.adjustment_amount < 0:
            return OperationType.WITHDRAWAL
        return OperationType.NONE
