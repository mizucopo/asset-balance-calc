"""JSON設定ファイル読み込みモジュール"""

import json
from decimal import Decimal, InvalidOperation
from typing import Any

from src.models.asset import Asset
from src.models.asset_raw import AssetRaw
from src.models.config import Config
from src.models.config_raw import ConfigRaw


class JsonLoader:
    """JSON設定ファイルの読み込みと変換を行う"""

    def parse_amount(self, value: str, allow_negative: bool = False) -> Decimal:
        """カンマ区切りの数値文字列をDecimalに変換する

        Args:
            value: カンマ区切りの数値文字列（例: "1,000,000"）
            allow_negative: 負の値を許可するかどうか

        Returns:
            変換後のDecimal値

        Raises:
            ValueError: 無効な数値形式、
                または負の値が許可されていない時に負の値が渡された場合
        """
        try:
            result = Decimal(str(value).replace(",", ""))
        except InvalidOperation as e:
            raise ValueError(f"無効な数値形式です: {value}") from e
        if not allow_negative and result < 0:
            raise ValueError(f"金額は正の値である必要があります: {value}")
        if result != result.to_integral_value():
            raise ValueError(f"金額は整数である必要があります: {value}")
        return result

    def convert_to_config(self, raw_data: ConfigRaw) -> Config:
        """ConfigRawをConfigに変換する

        Args:
            raw_data: 変換元のConfigRawオブジェクト

        Returns:
            変換後のConfigオブジェクト
        """
        adjustment_amount = self.parse_amount(
            raw_data.adjustment_amount, allow_negative=True
        )

        assets = tuple(
            Asset(
                name=asset.name,
                amount=self.parse_amount(asset.amount),
                rate=self._parse_rate(asset.rate),
            )
            for asset in raw_data.assets
        )

        for asset in assets:
            if asset.rate <= 0:
                raise ValueError(
                    f"目標配分割合は正の値である必要があります: "
                    f"{asset.name}={asset.rate}"
                )

        total_rate = sum(asset.rate for asset in assets)
        if total_rate != Decimal("1"):
            raise ValueError(
                f"目標配分割合の合計が1.0ではありません（合計: {total_rate}）"
            )

        return Config(
            adjustment_amount=adjustment_amount,
            assets=assets,
        )

    def _parse_rate(self, value: str) -> Decimal:
        """rate文字列をDecimalに変換する

        Args:
            value: rate文字列

        Returns:
            変換後のDecimal値

        Raises:
            ValueError: 無効なrate形式の場合
        """
        try:
            return Decimal(str(value))
        except InvalidOperation as e:
            raise ValueError(f"無効な数値形式です: {value}") from e

    def load_json(self, filename: str = "./config/config.json") -> Config:
        """JSONファイルを読み込み、Configオブジェクトに変換する

        Args:
            filename: 設定ファイルのパス

        Returns:
            変換後のConfigオブジェクト
        """
        with open(filename, "r") as file:
            raw_data: ConfigRaw = json.load(file, object_hook=self._dict_to_config_raw)
        return self.convert_to_config(raw_data)

    @staticmethod
    def _is_config_raw_dict(data: dict[str, Any]) -> bool:
        """辞書がConfigRawとして有効か検証する

        Args:
            data: 検証対象の辞書

        Returns:
            有効なConfigRaw形式の場合True、そうでなければFalse
        """
        required_fields = ["adjustment_amount", "assets"]
        if not all(field in data for field in required_fields):
            return False

        if not isinstance(data["assets"], list):
            return False

        asset_fields = ["name", "amount", "rate"]
        return all(
            all(field in asset for field in asset_fields) for asset in data["assets"]
        )

    def _dict_to_config_raw(self, data: dict[str, Any]) -> ConfigRaw | dict[str, Any]:
        """辞書をConfigRawオブジェクトに変換する

        Args:
            data: 変換対象の辞書

        Returns:
            ConfigRawオブジェクト（トップレベルの場合）または元の辞書
        """
        if self._is_config_raw_dict(data):
            assets = tuple(
                AssetRaw(name=asset["name"], amount=asset["amount"], rate=asset["rate"])
                for asset in data["assets"]
            )
            return ConfigRaw(
                adjustment_amount=data["adjustment_amount"],
                assets=assets,
            )
        return data
