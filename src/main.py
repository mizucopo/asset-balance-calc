"""資産配分計算ツール"""

import logging
from dataclasses import replace

import click
from mizu_common import AssetService, LoggingConfigurator

from src.formatters import AssetFormatter
from src.json_loader import JsonLoader


@click.command()
@click.option(
    "-c",
    "--config",
    default="./config/config.json",
    help="設定ファイルのパス (デフォルト: ./config/config.json)",
    type=click.Path(exists=True),
)
def main(config: str) -> None:
    """資産配分計算ツール"""
    LoggingConfigurator(level=logging.INFO)
    logger = LoggingConfigurator.get_logger(__name__)

    logger.info("設定ファイルを読み込みます: %s", config)
    loader = JsonLoader()
    service = AssetService()
    formatter = AssetFormatter()

    loaded_config = loader.load_json(config)

    logger.info("資産配分計算を開始します")
    calculated = service.calculate_current_rates(loaded_config.assets)
    config_with_rates = replace(loaded_config, calculated_assets=calculated)

    print(formatter.format_current_summary(config_with_rates))

    logger.info(
        "資産配分調整を実行します (操作: %s)",
        loaded_config.operation_type.value,
    )
    result = service.adjust_assets(calculated, loaded_config.adjustment_amount)

    print(formatter.format_adjusted_summary(result))
    logger.info("計算が完了しました")


if __name__ == "__main__":
    main()
