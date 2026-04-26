"""資産調整ロジックモジュール"""

from dataclasses import replace
from decimal import ROUND_FLOOR, Decimal

from src.constants.operation_type import OperationType
from src.models.asset import Asset
from src.models.asset_calculation import AssetCalculation
from src.models.config import Config


class AssetService:
    """資産の配分調整を行う"""

    def update_current_rate(self, config: Config) -> Config:
        """各資産の現在配分比率を計算する

        Args:
            config: 設定データ

        Returns:
            現在配分比率が更新された設定データ
        """
        sum_amount = sum(asset.amount for asset in config.assets)
        existing_calc_map = {calc.asset.name: calc for calc in config.calculated_assets}

        new_calculated_assets = tuple(
            AssetCalculation(
                asset=asset,
                current_rate=(
                    Decimal("0") if sum_amount == 0 else asset.amount / sum_amount
                ),
                flow_amount=existing_calc_map.get(
                    asset.name, AssetCalculation(asset=asset)
                ).flow_amount,
            )
            for asset in config.assets
        )

        return replace(config, calculated_assets=new_calculated_assets)

    def adjust_assets(self, config: Config) -> Config:
        """操作タイプに応じて資産を調整する

        Args:
            config: 設定データ

        Returns:
            調整後の設定データ

        Raises:
            ValueError: 入出金時にcalculated_assetsが未設定の場合
        """
        match config.operation_type:
            case OperationType.DEPOSIT | OperationType.WITHDRAWAL:
                if not config.calculated_assets:
                    raise ValueError(
                        "calculated_assetsが未設定です。"
                        "update_current_rateを先に実行してください。"
                    )
                return self._allocate(config)
            case OperationType.NONE:
                return config

    def _allocate(self, config: Config) -> Config:
        """water-fillingで資産配分を調整する

        Args:
            config: 設定データ

        Returns:
            調整後の設定データ

        Raises:
            ValueError: final_totalが0以下の場合、
                または配分対象アセットが存在しない場合
        """
        current_total = sum(asset.amount for asset in config.assets)
        flow = config.adjustment_amount
        final_total = current_total + flow

        if final_total <= 0:
            raise ValueError("final total would be negative")

        direction = 1 if flow > 0 else -1
        exact_amounts = self._water_filling(config.assets, flow, final_total, direction)
        rounded_amounts = self._apply_largest_remainder(exact_amounts, flow)

        new_calculated_assets = []
        new_assets = []
        for calc, amount in zip(config.calculated_assets, rounded_amounts, strict=True):
            new_calc = self._update_asset(calc, amount)
            new_calculated_assets.append(new_calc)
            new_assets.append(new_calc.asset)

        return replace(
            config,
            assets=tuple(new_assets),
            calculated_assets=tuple(new_calculated_assets),
        )

    def _water_filling(
        self,
        assets: tuple[Asset, ...],
        flow: Decimal,
        final_total: Decimal,
        direction: int,
    ) -> list[Decimal]:
        """water-fillingで各アセットの正確なflow_amountを計算する

        direction=1 で入金（不足アセットの水位を上げる）、
        direction=-1 で出金（超過アセットの水位を下げる）。

        Args:
            assets: 資産リスト
            flow: 入出金額（正=入金、負=出金）
            final_total: 最終総額
            direction: 1=入金、-1=出金

        Returns:
            各アセットのflow_amount（Decimal、小数のまま）

        Raises:
            ValueError: 配分対象アセットが存在しない場合
        """
        items: list[tuple[int, Asset, Decimal]] = []
        for idx, asset in enumerate(assets):
            level = asset.amount / asset.rate
            is_target = (direction == 1 and level < final_total) or (
                direction == -1 and level > final_total
            )
            if is_target:
                items.append((idx, asset, level))

        if not items:
            msg = (
                "no underweight assets for deposit"
                if direction == 1
                else "no overweight assets for withdrawal"
            )
            raise ValueError(msg)

        items.sort(key=lambda x: direction * x[2])

        flow_amounts = [Decimal("0")] * len(assets)
        remaining = abs(flow)
        current_level = items[0][2]
        group_rate_sum = items[0][1].rate

        for i, (_idx, asset, _level) in enumerate(items):
            if i > 0:
                group_rate_sum += asset.rate

            next_level = items[i + 1][2] if i + 1 < len(items) else final_total
            level_delta = abs(next_level - current_level)
            cost = level_delta * group_rate_sum

            if cost <= remaining:
                for j in range(i + 1):
                    item_idx, item_asset, _ = items[j]
                    flow_amounts[item_idx] += direction * level_delta * item_asset.rate
                remaining -= cost
                current_level = next_level
            else:
                partial_delta = remaining / group_rate_sum
                for j in range(i + 1):
                    item_idx, item_asset, _ = items[j]
                    flow_amounts[item_idx] += (
                        direction * partial_delta * item_asset.rate
                    )
                break

        return flow_amounts

    def _apply_largest_remainder(
        self,
        exact_amounts: list[Decimal],
        flow: Decimal,
    ) -> list[Decimal]:
        """最大余剰法で端数処理を行う

        Args:
            exact_amounts: 正確な配分額のリスト（小数含む）
            flow: 入出金額の合計

        Returns:
            端数処理後の整数配分額のリスト（合計はflowと完全に一致）
        """
        abs_amounts = [abs(a) for a in exact_amounts]
        floored = [a.to_integral_value(rounding=ROUND_FLOOR) for a in abs_amounts]

        total_floored = sum(floored)
        remainder = abs(flow) - total_floored

        fracs = [(i, abs_amounts[i] - floored[i]) for i in range(len(abs_amounts))]
        fracs.sort(key=lambda x: -x[1])

        result = list(floored)
        for k in range(int(remainder)):
            idx, _ = fracs[k]
            result[idx] += Decimal("1")

        sign = Decimal("1") if flow > 0 else Decimal("-1")
        return [sign * r for r in result]

    def _update_asset(
        self, calc: AssetCalculation, amount: Decimal
    ) -> AssetCalculation:
        """アセットの金額とflow_amountを更新する

        Args:
            calc: 計算結果
            amount: 符号付き増減額（正=入金、負=出金）

        Returns:
            更新されたAssetCalculation
        """
        new_asset = replace(calc.asset, amount=calc.asset.amount + amount)
        return replace(calc, asset=new_asset, flow_amount=amount)
