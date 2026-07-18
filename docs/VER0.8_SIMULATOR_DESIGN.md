# KeibaOS Ver0.8 回収率シミュレーター設計

## 目的

過去レースを当時の情報だけで時系列再現し、既存の予想パイプラインと購入戦略を用いて購入結果を精算する。Strategyごとに回収率、的中率、券種別成績、最大ドローダウンを比較できる再現可能な検証基盤を設計する。

今回は設計のみを対象とする。実装、DB変更、既存の予想・候補生成・戦略ロジックの複製は行わない。既存の `PredictionPipeline`、`BetGenerator`、`BetStrategy` を再利用する。

初期実装の対象券種は単勝のみとする。馬連、ワイド、3連複は、予想時点の実組み合わせオッズと確定した完全な払戻表を取得・保存できるまで購入対象にしない。現行 `BetGenerator` の `combination_score` は実オッズによる期待値ではなく候補比較値であるため、組み合わせ券種のEVとして扱わない。

## 基本方針

- 購入額は1点あたり100円単位とする。初期実装は固定100円で、資金配分は対象外とする。
- 実現ROIの検証は確定払戻表だけを使用する。仮想EV、後知恵のオッズ、候補比較値から払戻を推定しない。
- 予想時点の実オッズを用いたEV戦略の検証は、単勝または完全な組み合わせオッズスナップショットが保存される券種だけで行う。
- 未来情報を検証できない入力は受け入れない（Fail Closed）。検証不能なデータセットでは正式ROIを算出しない。
- 取消、除外、同着、返還、降着、不成立の精算ルールは、仕様確定まで推測実装しない。対応外状態は `VOID` または `UNSUPPORTED` 相当として明示的に記録する。

## 用語とID

現行コードの `horse_id` は血統上の恒久的な馬IDではなく、`horses.id`、すなわち特定レースの出走行IDを表す。シミュレーター設計ではこの意味を明確にするため、外部公開モデルでは `race_entry_id` を使用する。既存モデルとの接続境界でのみ `horse_id`（=`race_entry_id`）へ変換する。

- 外部払戻・結果データの `horse_no` はレース内の馬番である。
- Providerは `race_id + horse_no` から内部 `race_entry_id` への対応を解決する。
- 単勝の選択は重複なし1件、馬連・ワイドは重複なし2件、3連複は重複なし3件とする。
- 組み合わせの `race_entry_id` は常に昇順タプルへ正規化する。

## 時刻モデルと未来情報遮断

すべての日時はtimezone-awareな `datetime` を使用する。DBにはUTC ISO 8601形式で保存し、CLI・レポート表示はAsia/Tokyoを基本とする。

### SimulationRaceInput

```python
@dataclass(frozen=True)
class SimulationRaceInput:
    race_id: int
    target_race_date: date
    scheduled_start_at: datetime
    information_cutoff: datetime
    pipeline_input: RacePredictionInput
    input_snapshot_audit: InputSnapshotAudit
```

制約は以下のとおり。

- `information_cutoff <= scheduled_start_at`
- 予想・購入処理順は `scheduled_start_at, race_id` の昇順
- 最大ドローダウン用の精算順は `settled_at, race_id` の昇順
- `input_snapshot_audit` はデータセット識別子、取得時刻、情報源、各入力の `available_at` / `observed_at` を保持する

初期実装から次を必須検証とする。

1. 各過去走について `past_race.race_date < target_race_date` であること。
2. 出走情報、過去走、オッズ、Strategyに渡す入力のすべてで `available_at` または `observed_at <= information_cutoff` であること。
3. 対象レースの確定着順、払戻、確定後オッズを予想・候補生成・戦略選定へ渡さないこと。
4. 欠損した当時のオッズを後日取得値で補完しないこと。

上記の検証に失敗した場合は `SimulationValidationError` とする。該当のStrategy・レースは `ERROR` または除外結果として記録し、正式ROIの分母・分子へ含めない。現行データに時点情報がなく検証不能な場合、そのデータセットは正式ROI検証に使用しない。

### InputSnapshotAudit と監査明細

```python
@dataclass(frozen=True)
class InputAuditEntry:
    input_type: str
    source: str
    source_id: str
    available_at: datetime | None
    observed_at: datetime | None
    race_entry_id: int | None

@dataclass(frozen=True)
class InputSnapshotAudit:
    dataset_id: str
    source: str
    captured_at: datetime
    entries: tuple[InputAuditEntry, ...]
```

すべての日時はtimezone-awareでなければならない。`available_at` と `observed_at` のどちらもない監査明細、または `race_entry_id` 変換に失敗した外部結果・払戻明細はFail Closedで拒否する。

## ファイル構成案

```text
scripts/
  simulation/
    __init__.py
    models.py                 # 入力、購入、結果、集計、監査モデル
    simulator.py              # Simulator
    providers.py              # ResultProvider / PayoutProvider の境界
    database_providers.py     # SQLite実装（後続）
    validation.py             # 時点・ID・券種のFail Closed検証
    metrics.py                # 集計・最大ドローダウン
  cli/
    run_simulation.py         # 過去検証CLI（後続）
tests/
  test_simulator.py
  test_simulation_validation.py
  test_simulation_metrics.py
  test_simulation_providers.py
  test_simulation_migrations.py
  test_run_simulation_cli.py
```

`prediction` パッケージの評価・候補・戦略モジュールは変更せず、シミュレーション固有の責務を `simulation` パッケージに閉じ込める。

## 主要モデル

### StrategyIdentity

同一のStrategyクラスに異なる設定を適用した実行を区別する。

```python
@dataclass(frozen=True)
class StrategyIdentity:
    strategy_id: str
    strategy_name: str
    strategy_config: StrategyConfig
    strategy_config_hash: str
```

- `strategy_name` はStrategyクラス名または人間向け名称。
- `strategy_id` は `strategy_name` と `strategy_config_hash` から生成する安定識別子。任意の明示IDを許す場合も、設定ハッシュは必ず保持する。
- `strategy_config_hash` は、StrategyConfigを決定的にシリアライズしてSHA-256を計算する。
- 決定的シリアライズは、省略されたデフォルト値を展開した完全な設定、設定スキーマバージョン、列挙値を文字列へ変換した値、ソート済み配列化した集合を含め、キーをソートしたUTF-8 JSON（空白なし）とする。ハッシュ対象に実行日時や環境依存値を含めない。
- 同じ意味の設定（既定値の省略と明示を含む）が同じハッシュになることをテストする。

### SimulationBet

1Strategy・1レース内で計上する購入点。

```python
@dataclass(frozen=True)
class SimulationBet:
    race_id: int
    strategy_id: str
    bet_type: str
    race_entry_ids: tuple[int, ...]
    stake: int
    recommendation_rank: int
    placed_at_cutoff: datetime
```

- `stake` は正の100円倍数のみ許可する。
- `race_entry_ids` は券種の必要件数・重複なし・昇順正規化を検証する。
- 監査用に候補順位・設定ハッシュ・予測スコアを別明細へ保持してよいが、精算時に書き換えない。

### SettlementStatus

```python
class SettlementStatus(str, Enum):
    SETTLED = "settled"      # 必要な結果・払戻表が完全で、購入を精算済み
    NO_BET = "no_bet"        # Strategyが購入候補を選ばなかった
    UNSETTLED = "unsettled"  # 払戻・結果が未取得または不完全
    VOID = "void"            # 取消・返還・不成立等で精算仕様が未対応
    ERROR = "error"          # 時点検証・Provider・実行エラー
    UNSUPPORTED = "unsupported"  # 券種または精算仕様が未対応
```

### SimulationResult

必ず**1Strategy・1レース単位**で記録する。1購入単位でも複数Strategy横断でもない。

```python
@dataclass(frozen=True)
class SimulationResult:
    race_id: int
    strategy_id: str
    bets: tuple[SimulationBet, ...]
    settlement_status: SettlementStatus
    exclusion_reason: str | None
    planned_investment: int
    settled_investment: int | None
    payout: int | None
    profit: int | None
    hit_bet_count: int
    settled_at: datetime | None
```

- `planned_investment` は生成済み買い目の合計であり、全状態で監査可能とする。`NO_BET` は必ず0。
- `SETTLED` の場合のみ `settled_investment`、`payout`、`profit` を整数で保持し、ROI集計へ含める。
- `UNSETTLED`、`VOID`、`ERROR`、`UNSUPPORTED` は精算金額をすべて `None` とする。不明な払戻を0円として保存しない。
- `NO_BET` は `planned_investment=0`、精算金額は0ではなく `None` とし、ROIの購入分母へ含めない。
- `UNSETTLED` は必要な結果または払戻表が未取得・不完全であることを表す。
- 複数券種を購入し、1券種でも必要な払戻表が不完全なら、初期方針ではレース全体を `UNSETTLED` としてROI集計から除外する。部分精算は行わない。
- `VOID` と `ERROR` は原因を `exclusion_reason` に必ず記録する。

### BetTypeSummary

券種別成績を表す正式な主要モデル。

```python
@dataclass(frozen=True)
class BetTypeSummary:
    bet_type: str
    bet_count: int
    hit_bet_count: int
    investment: int
    payout: int
    profit: int
    roi: float | None
    bet_hit_rate: float | None
```

### SimulationSummary

1つの `StrategyIdentity` と対象期間に対する集計。

```python
@dataclass(frozen=True)
class SimulationSummary:
    strategy_id: str
    strategy_name: str
    strategy_config_hash: str
    race_count: int
    settled_race_count: int
    unsettled_race_count: int
    no_bet_race_count: int
    void_race_count: int
    error_race_count: int
    unsupported_race_count: int
    purchased_race_count: int
    bet_count: int
    hit_bet_count: int
    hit_race_count: int
    investment: int
    payout: int
    profit: int
    roi: float | None
    bet_hit_rate: float | None
    race_hit_rate: float | None
    by_bet_type: Mapping[str, BetTypeSummary]
    maximum_drawdown: int
```

### SimulationRunContext、SimulationRunMetadata と SimulationReport

複数Strategy比較とレース別明細を保持する実行結果モデル。

```python
@dataclass(frozen=True)
class SimulationRunContext:
    run_id: str
    dataset_id: str
    started_at: datetime
    target_commit_id: str
    stake_per_bet: int
    supported_bet_types: tuple[str, ...]
    input_period_start: datetime
    input_period_end: datetime

@dataclass(frozen=True)
class SimulationRunMetadata:
    run_id: str
    dataset_id: str
    started_at: datetime
    completed_at: datetime
    target_commit_id: str
    stake_per_bet: int
    supported_bet_types: tuple[str, ...]

@dataclass(frozen=True)
class SimulationReport:
    metadata: SimulationRunMetadata
    strategy_identities: tuple[StrategyIdentity, ...]
    race_results: tuple[SimulationResult, ...]
    strategy_summaries: Mapping[str, SimulationSummary]
    official_roi_valid: bool
    validation_errors: tuple[SimulationValidationError, ...]
```

`SimulationRunContext` は入力専用であり、`completed_at` を持たない。Simulatorは実行完了時に `completed_at` を生成して `SimulationRunMetadata` を作る。`SimulationReport` は全Strategy・全レースの明細を保持する。`SimulationSummary` 単体をSimulatorの最終戻り値にしない。さらに `official_roi_valid: bool` と `validation_errors: tuple[SimulationValidationError, ...]` を保持する。

## Simulatorの入出力と既存パイプライン連携

```python
class Simulator:
    def run(
        self,
        race_inputs: Sequence[SimulationRaceInput],
        strategies: Sequence[StrategyIdentity],
        result_provider: ResultProvider,
        payout_provider: PayoutProvider,
        run_context: SimulationRunContext,
    ) -> SimulationReport:
        ...
```

処理は `scheduled_start_at, race_id` 順に行う。

1. `SimulationRaceInput` をFail Closedで検証する。
2. StrategyIdentityごとに、元のPipelineConfigをコピーし `strategy_config` を当該 `StrategyConfig` に差し替えた新しい `PipelineConfig` を生成する。
3. 生成したPipelineConfigで `PredictionPipeline` を1回実行する。
4. パイプラインが内部で生成した `Prediction`、`ValueEvaluation`、`BetRecommendation`、`BetPlan` をそのまま利用する。
5. `BetPlan` から `SimulationBet` を生成して払戻表と照合する。
6. 1Strategy・1レースごとの `SimulationResult` を作り、最後にStrategy別の `SimulationSummary` と `SimulationReport` を作る。

現行 `PredictionPipeline` は `BetGenerator` と `BetStrategy` まで内部実行する。Simulatorは候補生成・戦略選定を再実行せず、PipelineResult内の `BetPlan` だけを消費する。これにより通常実行とシミュレーションの購入ロジック乖離を防ぐ。

監査入力だけでは未来情報遮断として不十分である。Pipelineと各Engineは `reference_datetime=information_cutoff` を受け取るか、現在時刻・現在DBを参照しない純粋処理でなければならない。内部DB検索を行う場合は必ず `as-of information_cutoff` 条件を使用する。Strategyごとに新しいPipelineインスタンスを生成するか、完全なステートレス性を保証し、可変オブジェクト・キャッシュをStrategy間で共有しない。この契約は初期実装の必須検証とする。

データセット全体に時点監査情報がない場合は実行を拒否する。個別レースの未来情報検出は `ERROR` 結果として記録する。ERRORが1件でもあるReportは初期方針で `official_roi_valid=False` とする。ERRORを除外して算出する値は診断用ROIとしてのみ表示し、正式ROIと混同しない。

## ResultProvider と PayoutProvider

### ResultProvider

確定着順とレース状態をレース単位で返す。

```python
class ResultProvider(Protocol):
    def get_result(self, race_id: int) -> RaceResultTable | None:
        ...
```

```python
@dataclass(frozen=True)
class RaceResultEntry:
    horse_no: int
    race_entry_id: int
    finish_position: int | None
    result_status: str

@dataclass(frozen=True)
class RaceResultTable:
    race_id: int
    is_complete: bool
    finalized_at: datetime | None
    observed_at: datetime
    source: str
    entries: tuple[RaceResultEntry, ...]
```

`RaceResultTable` はtimezone-awareな `finalized_at` / `observed_at`、完全性、情報源、各 `horse_no` の着順・状態を保持する。Providerは外部 `horse_no` を内部 `race_entry_id` へ変換する責務を持つ。変換できない明細はFail ClosedでERRORとし、別レースの `race_entry_id` を関連付けてはならない。

### PayoutProvider

個別買い目への `Payout | None` では、不的中とデータ未取得を区別できないため採用しない。レース・券種単位の完全な払戻表を返す。

```python
class PayoutProvider(Protocol):
    def get_payout_table(
        self,
        race_id: int,
        bet_type: str,
    ) -> PayoutTable | None:
        ...
```

```python
@dataclass(frozen=True)
class PayoutTable:
    race_id: int
    bet_type: str
    is_complete: bool
    finalized_at: datetime | None
    observed_at: datetime | None
    source: str | None
    winning_combinations: Mapping[tuple[int, ...], PayoutEntry]
    refund_entries: Mapping[tuple[int, ...], RefundEntry]
```

```python
@dataclass(frozen=True)
class PayoutEntry:
    race_entry_ids: tuple[int, ...]
    payout_per_100: int
    payout_status: str

@dataclass(frozen=True)
class RefundEntry:
    race_entry_ids: tuple[int, ...]
    refund_per_100: int
    reason: str
```

- `winning_combinations` は的中組み合わせ、100円あたり払戻額、同着等の状態を保持する。
- `refund_entries` は返還対象と返還額を保持する。
- `is_complete=True` の払戻表に購入組み合わせが存在しない場合だけ、不的中（払戻0円）と判定する。
- 払戻表が未取得、`is_complete=False`、または結果表が不完全の場合は該当券種を精算不能とする。
- 複数券種を購入し1券種でも必要データが不完全な場合、初期方針ではレース全体を `UNSETTLED` とし、投資額・払戻額をROIへ混入させない。
- `observed_at` は取得・監査時刻であり、資金曲線の精算時刻には使用しない。`SETTLED` の `settled_at` は、結果表と全必要払戻表の `finalized_at` の最大値とする。必要な `finalized_at` が取得できない場合、その結果は正式ドローダウンへ含めない。

## 集計指標と分母

| 指標 | 定義 |
| --- | --- |
| 対象レース数 (`race_count`) | 全 `SimulationRaceInput` 件数。 |
| 精算済みレース数 | `SETTLED` のレース数。 |
| 未精算レース数 | `UNSETTLED` のレース数。 |
| 購入なしレース数 | `NO_BET` のレース数。 |
| Voidレース数 | `VOID` のレース数。 |
| Errorレース数 | `ERROR` のレース数。 |
| Unsupportedレース数 | `UNSUPPORTED` のレース数。 |
| 購入レース数 | `SETTLED` かつ購入点が1点以上のレース数。 |
| 購入点数 | 精算済み購入の全点数。 |
| 的中購入点数 | 精算済み購入のうち払戻額が0円超の点数。 |
| 的中レース数 | 精算済み購入レースのうち1点以上的中したレース数。 |
| 投資額 | `SETTLED` かつ購入ありの投資額合計。 |
| 払戻額 | `SETTLED` かつ購入ありの払戻額合計。 |
| 収支 | `払戻額 - 投資額`。 |
| ROI | `払戻額 ÷ 投資額 × 100`。投資額0の場合は `None`、表示は `N/A`。 |
| bet_hit_rate | `的中購入点数 ÷ 精算済み購入点数 × 100`。分母0なら `None`。 |
| race_hit_rate | `1点以上的中した精算済み購入レース数 ÷ 精算済み購入レース数 × 100`。分母0なら `None`。 |
| 最大ドローダウン | `settled_at, race_id` 順の累積収支で計算する最大下落額。初期peakは0円。 |

`hit_bet_count` は `payout_status == winning` の購入点だけを数える。返還、Void、Unsupportedは払戻額が正でも的中点に含めない。`hit_race_count` はwinning購入点が1件以上ある精算済み購入レース数とする。

各状態は排他的であり、`SETTLED + NO_BET + UNSETTLED + VOID + ERROR + UNSUPPORTED` の件数合計は必ず `race_count` と一致する。未精算・Void・Error・Unsupportedレースの精算金額はROI、的中率、ドローダウンへ混入させない。各件数は隠さずレポートとCLIへ表示する。

最大ドローダウンは精算済みレースだけを順に処理し、初期 `equity = 0`、初期 `peak = 0` とする。各精算後に `equity += profit`、`peak = max(peak, equity)`、`drawdown = peak - equity` を計算し、その最大値を保持する。

## 実現ROIとEV戦略の区別

- **実現ROI検証**：確定した完全な払戻表により、実際に購入した点を精算する。初期実装は単勝だけを対象とする。
- **EV戦略検証**：予想時点の実オッズスナップショットと校正済みまたは明示的に暫定である確率を用いる。組み合わせ券種のEV条件は、予想時点の実組み合わせオッズが取得・監査可能になるまで実行しない。
- `combination_score` は候補比較値であり、実現ROI・EVのどちらにも直接代入しない。

## DBマイグレーション案

既存テーブルを破壊せず、取得単位の完全性を親テーブルで、組み合わせと選択馬を関連テーブルで表す。接続作成時に `PRAGMA foreign_keys = ON` を必須とする。

```sql
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE race_results (
    race_id INTEGER PRIMARY KEY,
    result_status TEXT NOT NULL,
    finalized_at TEXT,
    observed_at TEXT NOT NULL,
    source TEXT NOT NULL,
    source_url TEXT,
    CHECK (result_status IN ('complete', 'partial', 'void', 'unsupported')),
    FOREIGN KEY (race_id) REFERENCES races(id)
);

CREATE TABLE race_result_entries (
    race_id INTEGER NOT NULL,
    race_entry_id INTEGER NOT NULL,
    finish_position INTEGER,
    result_status TEXT NOT NULL,
    PRIMARY KEY (race_id, race_entry_id),
    FOREIGN KEY (race_id) REFERENCES races(id),
    FOREIGN KEY (race_entry_id) REFERENCES horses(id),
    CHECK (finish_position IS NULL OR finish_position > 0),
    CHECK (result_status IN ('finished', 'cancelled', 'excluded', 'void', 'unsupported'))
);

CREATE TABLE odds_snapshot_batches (
    id INTEGER PRIMARY KEY,
    race_id INTEGER NOT NULL,
    bet_type TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    is_complete INTEGER NOT NULL,
    source TEXT NOT NULL,
    source_url TEXT,
    CHECK (is_complete IN (0, 1)),
    FOREIGN KEY (race_id) REFERENCES races(id),
    UNIQUE (race_id, bet_type, observed_at, source)
);

CREATE TABLE odds_snapshots (
    id INTEGER PRIMARY KEY,
    batch_id INTEGER NOT NULL,
    bet_type TEXT NOT NULL,
    selection_key TEXT NOT NULL,
    odds_decimal TEXT NOT NULL,
    FOREIGN KEY (batch_id) REFERENCES odds_snapshot_batches(id),
    CHECK (length(odds_decimal) > 0),
    UNIQUE (batch_id, bet_type, selection_key)
);

CREATE TABLE odds_snapshot_selections (
    odds_snapshot_id INTEGER NOT NULL,
    race_entry_id INTEGER NOT NULL,
    selection_order INTEGER NOT NULL,
    PRIMARY KEY (odds_snapshot_id, race_entry_id),
    FOREIGN KEY (odds_snapshot_id) REFERENCES odds_snapshots(id),
    FOREIGN KEY (race_entry_id) REFERENCES horses(id),
    CHECK (selection_order > 0),
    UNIQUE (odds_snapshot_id, selection_order)
);

CREATE TABLE payout_publications (
    id INTEGER PRIMARY KEY,
    race_id INTEGER NOT NULL,
    bet_type TEXT NOT NULL,
    finalized_at TEXT,
    observed_at TEXT NOT NULL,
    is_complete INTEGER NOT NULL,
    source TEXT NOT NULL,
    source_url TEXT,
    CHECK (is_complete IN (0, 1)),
    FOREIGN KEY (race_id) REFERENCES races(id),
    UNIQUE (race_id, bet_type, observed_at, source)
);

CREATE TABLE payouts (
    id INTEGER PRIMARY KEY,
    publication_id INTEGER NOT NULL,
    bet_type TEXT NOT NULL,
    selection_key TEXT NOT NULL,
    payout_per_100 INTEGER NOT NULL,
    payout_status TEXT NOT NULL,
    FOREIGN KEY (publication_id) REFERENCES payout_publications(id),
    CHECK (payout_per_100 >= 0),
    CHECK (payout_status IN ('winning', 'refund', 'void', 'unsupported')),
    UNIQUE (publication_id, bet_type, selection_key)
);

CREATE TABLE payout_selections (
    payout_id INTEGER NOT NULL,
    race_entry_id INTEGER NOT NULL,
    selection_order INTEGER NOT NULL,
    PRIMARY KEY (payout_id, race_entry_id),
    FOREIGN KEY (payout_id) REFERENCES payouts(id),
    FOREIGN KEY (race_entry_id) REFERENCES horses(id),
    CHECK (selection_order > 0),
    UNIQUE (payout_id, selection_order)
);

CREATE INDEX idx_result_entries_race ON race_result_entries(race_id);
CREATE INDEX idx_odds_batches_race_time ON odds_snapshot_batches(race_id, observed_at);
CREATE INDEX idx_payout_publications_race_time ON payout_publications(race_id, observed_at);
CREATE INDEX idx_payouts_publication_type ON payouts(publication_id, bet_type);
```

払戻なし（完全な払戻表に該当組み合わせが存在しない）と、払戻データ未取得・不完全（publicationなしまたは `is_complete=0`）を明確に区別する。

`odds_snapshot_batches` と `payout_publications` は券種単位の親レコードであるため、単勝は完全・馬連は未取得のような状態を表現でき、PayoutProviderの `race_id + bet_type` 境界と一致する。`selection_key` は関連テーブルの昇順 `race_entry_id` 列から決定的に生成し、監査と一意制約に使う。参照整合性は関連テーブルで維持し、selection_keyだけに依存しない。

`race_result_entries`、`odds_snapshot_selections`、`payout_selections` の `race_entry_id` が対象 `race_id` に属することは、複合外部キーを導入できる場合はDB制約で、できない場合はProviderのFail Closed検証で保証する。別レースの出走行IDを関連付けた場合は登録・精算を拒否する。

オッズは浮動小数点REALで保存せず、Decimal互換の正規化TEXT（`odds_decimal`）または明示的な整数スケール値で保存する。Pythonでは `Decimal` として読み書きし、往復精度をテストする。

マイグレーションは連番の `schema_migrations` で管理し、各バージョンをトランザクションで適用する。マイグレーションテストは本番 `database/keiba.db` を直接使わず、一時DBパスまたは注入可能なConnection Factoryを使用する。

## CLI実行案

```bash
python -m scripts.cli.run_simulation \
  --from 2025-01-01T00:00:00+09:00 \
  --to 2025-12-31T23:59:59+09:00 \
  --strategy-config config/strategy/default.json \
  --stake 100 \
  --bet-types "単勝" \
  --output reports/simulation-v0.8.json
```

CLIは以下を行う。

1. 期間、StrategyConfig、購入単位、券種、時点検証可能なデータセットを検証する。
2. 未対応券種が指定された場合は明確なエラーまたは `unsupported` を返す。初期実装では単勝以外を実行しない。
3. ProviderからFail Closed条件を満たす `SimulationRaceInput` を取得する。
4. `Simulator` を実行し、未精算・Void・Error・Unsupported件数と、正式ROIが無効かを黙って捨てず表示する。
5. JSON/CSVへレポートとレース別明細を出力する。

出力JSON/CSVには最低限、`strategy_id`、`strategy_config_hash`、対象コミットID、データセット識別子、`information_cutoff`、`settlement_status`、除外理由を含める。ROI・的中率の分母が0なら `null` / `N/A` とする。

## テスト方針

### 単体テスト

- 100円単位以外の購入額、券種ごとの選択件数、重複選択を拒否する。
- 完全な払戻表に購入組み合わせがない不的中と、払戻表未取得を区別する。
- `is_complete=False` の払戻表、または複数券種の一部払戻表欠損がROIへ含まれない。
- 同じStrategyクラス・異なるStrategyConfigが異なる `strategy_id` / `strategy_config_hash` / 集計へ分離される。
- `scheduled_start_at` と `settled_at` の順序が異なる場合、予想順とドローダウン順がそれぞれの規則に従う。
- 初期peak=0円を含む最大ドローダウンを検証する。
- 未来情報を1件でも検出した場合、Fail Closedで `SimulationValidationError` とし、ERRORまたは除外結果になる。
- `horse_no` から `race_entry_id` への変換と、組み合わせ昇順正規化を検証する。
- 同着、返還、不成立は仕様確定まで `VOID` または `unsupported` と明示し、推測精算しない。
- 投資額0・精算済み購入点数0のROI・各的中率が `None` になる。
- Simulatorが `completed_at` を生成し、入力のRunContextが完了時刻を持たない。
- UNSETTLEDの `payout` / `profit` が `None` となる。
- UNSUPPORTEDとERRORが別集計となる。
- 返還を的中扱いしない。
- 券種ごとの払戻・オッズ完全性を独立して判定する。
- 同一組み合わせの重複登録を拒否する。
- 別レースの `race_entry_id` 関連付けを拒否する。
- Pipeline内部の現在時刻・現在DB参照を検出し、as-of契約違反を拒否する。
- ERRORが1件以上あるReportで `official_roi_valid=False` になる。
- DecimalオッズをDBから往復して精度を失わない。

### 統合テスト

- 固定Fixtureで `PredictionPipeline` → 内部 `BetGenerator` / `BetStrategy` → `Simulator` → 完全払戻表の一連を検証する。
- SimulatorがPipeline内の `BetPlan` を使用し、候補生成・戦略判定を重複実行しないことを確認する。
- 同一入力へ複数StrategyConfigを適用し、明細・集計・資金曲線が独立することを確認する。
- 時点監査情報のないデータセットで正式ROIが拒否されることを確認する。
- DBマイグレーションは一時DBまたはConnection Factoryを使い、本番 `database/keiba.db` を変更しないことを確認する。
- CLIの終了コード、unsupported券種、未精算・除外表示、JSON/CSV監査列をE2Eで確認する。

## 実装順序

1. timezone-awareな時点監査モデル、StrategyIdentity、SimulationResult、SimulationReport、Fail Closed検証を実装する。
2. 結果・払戻・オッズの親子テーブルと一時DBによるマイグレーションテストを追加する。
3. ResultProvider / PayoutProviderの抽象境界とインメモリFixture実装を追加する。
4. 単勝のみを対象に、100円購入、完全払戻表による精算、集計、最大ドローダウンを実装する。
5. 複数StrategyConfigの比較実行、決定的設定ハッシュ、JSON/CSV監査出力を追加する。
6. CLIとSQLite Providerを追加し、データ不足・未対応券種を明示する。
7. 実組み合わせオッズ・完全払戻表の取得後、馬連、ワイド、3連複を順に追加する。

## 未確定事項

- オッズ・払戻・確定結果の公式取得元、利用規約、保存頻度、再取得方針。
- 予想時点を発走直前、出馬表公開時、または固定時刻のどれに定義するか。
- 取消、除外、同着、返還、降着、不成立の券種別精算規則。
- 払戻表の完全性を情報源ごとにどのように判定するか。
- 未精算レースを将来部分精算するか、常にレース全体除外とするか。
- 複数Strategy比較時の資金曲線を独立資金とするか、共通資金とするか。
- 現行データへ `available_at` / `observed_at` をどの履歴から補完可能か。

未確定の精算ルールは、実装時に推測で補わない。仕様が確定するまで `VOID`、`UNSETTLED`、または `unsupported` として明示的に扱う。
