# asset-balance-calc

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

## 出力順

現在と調整後の資産配分は、追加額または出金額の絶対値が大きい銘柄から
同じ順序で出力されます。同額の場合は設定ファイルの順序を維持します。
調整額が0円の場合も設定ファイルの順序で出力されます。

## 開発

```sh
# テスト・リント・型チェック（一括）
uv run task test

# 個別実行
uv run pytest
uv run mypy
uv run ruff check src tests stubs
uv run ruff format src tests stubs
```

## ブランチ戦略

- `main`: 本番
- `develop`: 開発
- `feature/*`: 機能
