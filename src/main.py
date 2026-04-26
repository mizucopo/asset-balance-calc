"""資産配分計算ツール"""

import click

from src.formatters import AssetFormatter
from src.json_loader import JsonLoader
from src.services.asset_service import AssetService


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
    loader = JsonLoader()
    service = AssetService()
    formatter = AssetFormatter()

    data = loader.load_json(config)
    data = service.update_current_rate(data)

    print(formatter.format_current_summary(data))

    data = service.adjust_assets(data)
    data = service.update_current_rate(data)

    print(formatter.format_adjusted_summary(data))


if __name__ == "__main__":
    main()
