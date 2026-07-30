"""フォーマット処理モジュール"""

from mizu_common import AssetAdjustmentResult, AssetAdjustmentType, AssetCalculation

from src.models.config import Config


class AssetFormatter:
    """資産情報のフォーマット処理を行う"""

    def format_current_summary(
        self,
        config: Config,
        result: AssetAdjustmentResult,
    ) -> str:
        """現在の資産配分サマリーを生成する

        Args:
            config: 設定データ
            result: 資産調整結果

        Returns:
            フォーマットされたサマリー文字列
        """
        lines = ["", "現在の資産配分"]
        lines.extend(
            self._format_asset_current(config.calculated_assets[index])
            for index in self._get_prioritized_indices(result)
        )
        return "\n".join(lines)

    def format_adjusted_summary(self, result: AssetAdjustmentResult) -> str:
        """調整後の資産配分サマリーを生成する

        Args:
            result: 資産調整結果

        Returns:
            フォーマットされたサマリー文字列
        """
        title = self._get_adjusted_title(result.operation_type)
        lines = ["", title]
        lines.extend(
            self._format_asset_adjusted(
                result.calculated_assets[index],
                result.operation_type,
            )
            for index in self._get_prioritized_indices(result)
        )
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _get_prioritized_indices(
        result: AssetAdjustmentResult,
    ) -> tuple[int, ...]:
        """入出金額の絶対値が大きい順のインデックスを返す

        Args:
            result: 資産調整結果

        Returns:
            優先順に並べたインデックス
        """
        return tuple(
            sorted(
                range(len(result.calculated_assets)),
                key=lambda index: abs(result.calculated_assets[index].flow_amount),
                reverse=True,
            )
        )

    @staticmethod
    def _format_asset_current(calc: AssetCalculation) -> str:
        """現在の資産情報をフォーマットする

        Args:
            calc: 資産計算データ

        Returns:
            フォーマットされた資産情報文字列
        """
        return (
            f"  {calc.asset.name}\n"
            f"    資産額: {int(calc.asset.amount):,}円\n"
            f"      割合: {calc.current_rate:.2%}"
        )

    def _format_asset_adjusted(
        self, calc: AssetCalculation, operation_type: AssetAdjustmentType
    ) -> str:
        """調整後の資産情報をフォーマットする

        Args:
            calc: 資産計算データ
            operation_type: 操作タイプ

        Returns:
            フォーマットされた資産情報文字列
        """
        lines = [f"  {calc.asset.name}"]
        match operation_type:
            case AssetAdjustmentType.DEPOSIT:
                lines.append(f"    追加額: {int(calc.flow_amount):,}円")
            case AssetAdjustmentType.WITHDRAWAL:
                lines.append(f"    出金額: {int(abs(calc.flow_amount)):,}円")
        lines.append(f"    資産額: {int(calc.asset.amount):,}円")
        lines.append(f"      割合: {calc.current_rate:.2%}")
        return "\n".join(lines)

    @staticmethod
    def _get_adjusted_title(operation_type: AssetAdjustmentType) -> str:
        """操作タイプに応じたタイトルを返す

        Args:
            operation_type: 操作タイプ

        Returns:
            タイトル文字列
        """
        match operation_type:
            case AssetAdjustmentType.DEPOSIT:
                return "追加入金後の資産配分:"
            case AssetAdjustmentType.WITHDRAWAL:
                return "出金後の資産配分:"
            case AssetAdjustmentType.NONE:
                return "資産配分:"
