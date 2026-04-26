# AssetCalc

資産配分計算ツール。目標配分割合に基づいて入出金額を各資産に配分します。

## 前提条件

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)

## セットアップ

```sh
uv sync
```

## 使い方

```sh
uv run task run
```

オプション:
- `-c, --config` 設定ファイルのパス (デフォルト: `./config/config.json`)

## 設定ファイル

```json
{
  "adjustment_amount": "100,000",
  "assets": [
    {"name": "株式", "amount": "60,000,000", "rate": "0.60"},
    {"name": "債券", "amount": "40,000,000", "rate": "0.40"}
  ]
}
```

- `adjustment_amount`: 調整額（正=入金、負=出金）
- `assets[].rate`: 目標配分割合（合計=1.0）

## 開発

```sh
# テスト・リント・型チェック（一括）
uv run task test

# 個別実行
uv run pytest ./tests
uv run mypy ./src
uv run ruff check ./src
uv run ruff format ./src
```

## ブランチ戦略

- `main`: 本番
- `develop`: 開発
- `feature/*`: 機能
