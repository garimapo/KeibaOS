# KeibaOS

## Persisted simulation request CLI

Persisted simulation requests are executed through the approved request application boundary:

```bash
python -m scripts.cli.run_persisted_simulation <request_path>
```

`<request_path>` is the request JSON file. A relative `database_path` in that file is anchored to the
request file's parent directory. A successful run writes one deterministic JSON document to stdout and
returns exit code `0`. Expected request, validation, or SQLite errors write one deterministic JSON error
document to stderr and return exit code `1`. Native argparse usage errors return `2`; `--help` exits `0`.

Rates represented by `Decimal` are emitted as fixed-point JSON strings, or `null` where no denominator
exists. This tool is for research and verification only; it does not guarantee profit or performance.

KeibaOS は、取得済みの競馬レース・出走馬・過去走データをもとに、馬ごとの総合評価、暫定的な単勝期待値、買い目候補を生成する Python プロジェクトです。

> Ver0.7 では予想パイプラインとCLI実行を提供します。確率校正、券種別の実オッズ期待値、資金配分・自動購入は対象外です。

## 主な機能

- SQLite へのレース・出走馬・過去走の保存と互換マイグレーション
- Beautiful Soup を利用した過去走テーブル解析
- 能力・展開・騎手・コース適性を統合した総合スコア
- スコアをsoftmax変換した暫定推定勝率と単勝推定EV
- 単勝、馬連、ワイド、3連複の候補生成
- 設定可能な候補抽出戦略
- 1レースをCLIから実行する統合パイプライン

## 必要環境

- Python 3.12 以降
- SQLite（Python標準ライブラリの `sqlite3` を使用）

## セットアップ

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

macOS / Linux:

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## テスト

全テストはpytestで実行します。

```bash
python -m pytest -v
```

標準ライブラリのunittest形式で実行する場合は次のとおりです。

```bash
python -m unittest discover -s tests -v
```

## CLIでの予想実行

CLIは保存済みのSQLiteデータを読み取り、`PredictionPipeline` を実行します。

```bash
python -m scripts.cli.run_prediction <race_id>
```

戦略設定は任意です。

```bash
python -m scripts.cli.run_prediction 37 \
  --bet-types "単勝,馬連,ワイド" \
  --max-bets 10 \
  --max-candidates 50 \
  --style formation \
  --min-combination-score 0.0 \
  --sort generator_rank
```

主なオプション:

- `--bet-types`: 対象券種をカンマ区切りで指定
- `--max-bets`: 戦略が抽出する最大購入点数
- `--max-candidates`: 戦略が考慮する最大候補数
- `--style`: `box` または `formation`
- `--min-combination-score`: 組み合わせ候補の比較値下限
- `--sort`: `generator_rank`、`combination_score`、`prediction_score`、`estimated_probability`

出力には、総合順位・総合スコア・暫定推定勝率・単勝推定EV・戦略抽出後の買い目候補が含まれます。ログは標準エラー出力へ表示されます。

## 予想パイプライン

`scripts/prediction/prediction_pipeline.py` は、DB・HTTP通信を直接行わない統合層です。

1. `AbilityEngine`
2. `PaceEngine`
3. `JockeyEngine`
4. `TrackEngine`
5. `Predictor`
6. `ValueEngine`
7. `BetGenerator`
8. `BetStrategy`

各段階の中間結果は `PipelineResult` に保持されます。段階で例外が発生した場合は、段階名を持つ `PipelineExecutionError` が送出されます。

## ディレクトリ構成

```text
scripts/
  cli/                 # CLIエントリーポイント
  parsers/             # HTML解析
  prediction/          # 評価・候補・戦略・統合パイプライン
  database.py          # SQLite永続化とマイグレーション
tests/                 # 単体・E2Eテスト
.github/workflows/     # CI
```

## 注意事項と今後の課題

- `estimated_win_probability` は総合スコアをsoftmax変換した校正前の暫定推定値であり、実測勝率ではありません。
- 単勝以外の候補比較値は実オッズを使った期待値ではありません。
- 購入判断、資金配分、市場控除率、実績データによる確率校正は未実装です。
- 本プロジェクトの出力は研究・検証用途であり、利益を保証するものではありません。
