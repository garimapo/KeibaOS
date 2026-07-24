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
    providers/                # RawデータをRepository境界モデルへ変換するProvider契約
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
    by_bet_type: Mapping[str, BetTypeSummary]
```

- `planned_investment` は生成済み買い目の合計であり、全状態で監査可能とする。`NO_BET` は必ず0。
- `SETTLED` の場合のみ `settled_investment`、`payout`、`profit` を整数で保持し、ROI集計へ含める。
- `UNSETTLED`、`VOID`、`ERROR`、`UNSUPPORTED` は精算金額をすべて `None` とする。不明な払戻を0円として保存しない。
- `NO_BET` は `planned_investment=0`、精算金額は0ではなく `None` とし、ROIの購入分母へ含めない。
- `UNSETTLED` は必要な結果または払戻表が未取得・不完全であることを表す。
- 複数券種を購入し、1券種でも必要な払戻表が不完全なら、初期方針ではレース全体を `UNSETTLED` としてROI集計から除外する。部分精算は行わない。
- `VOID` と `ERROR` は原因を `exclusion_reason` に必ず記録する。
- `by_bet_type` は `BetTypeSummary` を券種キーで保持する不変Mappingであり、原子評価の払戻status・照合明細・odds等は保持しない。
- `SETTLED` では `by_bet_type` が購入券種集合と完全一致し、各券種の生成数・精算数・投資額と全体の `bets`／`planned_investment` に一致する。券種別の的中数・投資額・払戻額・収支の合計も、結果全体の値と一致する。
- `NO_BET` の `by_bet_type` は空とする。購入がある `UNSETTLED`、`VOID`、`ERROR`、`UNSUPPORTED` は購入券種ごとの件数を保持するが、券種別の精算数・的中数・投資額・払戻額・収支はすべて0、率は `None` とする。購入がない `ERROR` は空Mappingを許可し、空の `UNSETTLED`、`VOID`、`UNSUPPORTED` は許可しない。
- `SimulationSummary` は各 `SimulationResult.by_bet_type` を再集計できる。`SimulationResult` 自身は集計済みの券種別値だけを保持し、原子評価の詳細を再構築しない。

### BetTypeSummary

券種別成績を表す正式な主要モデル。`SimulationResult` と `SimulationSummary` の双方で再利用する。

```python
@dataclass(frozen=True)
class BetTypeSummary:
    bet_type: str
    bet_count: int
    settled_bet_count: int
    hit_bet_count: int
    investment: int
    payout: int
    profit: int
    roi: Decimal | None
    bet_hit_rate: Decimal | None
```

`bet_count` は生成した全買い目数、`settled_bet_count` は正常精算された買い目数、`hit_bet_count` は精算済み買い目のうち winning となった点数とする。`bet_hit_rate` の分母は `settled_bet_count` とする。

初期対応券種は `単勝`、`馬連`、`ワイド`、`3連複` とし、各 `SimulationBet` は1つの券種・1つの正規化済み選択組合せを表す原子的な買い目とする。

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
    bet_count: int
    settled_bet_count: int
    settled_purchase_race_count: int
    hit_bet_count: int
    hit_race_count: int
    investment: int
    payout: int
    profit: int
    roi: Decimal | None
    bet_hit_rate: Decimal | None
    race_hit_rate: Decimal | None
    by_bet_type: Mapping[str, BetTypeSummary]
    maximum_drawdown: int
```

`SimulationSummary` は、strategy identityを明示入力として受け取る純粋な `_build_simulation_summary()` が `SimulationResult` 列から構築する。

```python
def _build_simulation_summary(
    *,
    strategy_id: str,
    strategy_name: str,
    strategy_config_hash: str,
    results: Sequence[SimulationResult],
) -> SimulationSummary:
    ...
```

`target_race_count` は実モデルの `race_count` に対応し、全statusの結果数とする。`settled_purchase_race_count` は `SETTLED` かつ買い目を持つレース数、`bet_count` は全statusの `bets` 件数、`settled_bet_count`・金額・ROI・的中率は `SETTLED` のみを集計対象とする。

率はすべて `Decimal | None` で、ROIは `payout / investment × 100`、券種別的中率は `hit_bet_count / settled_bet_count × 100`、レース的中率は `hit_race_count / settled_purchase_race_count × 100` とする。分母が0なら `None` とし、floatへ変換しない。

最大ドローダウンは `SETTLED` 結果だけを新しい列へ抽出して `(settled_at, race_id)` 昇順で並べ、初期peakを0として累積収支の最大下落幅を計算する。NO_BETと非精算statusは含めず、入力列をin-placeで並べ替えない。`by_bet_type` は各結果の同名Mappingを券種ごとに再集計し、全体の件数・金額・収支と一致しなければならない。原子評価の照合明細はSummaryへ保持しない。

### SimulationRunContext、SimulationRunMetadata と SimulationReport

複数Strategy比較とレース別明細を保持する実行結果モデル。

```python
@dataclass(frozen=True)
class SimulationRunContext:
    run_id: str
    dataset_id: str
    started_at: datetime
    target_commit_id: str

@dataclass(frozen=True)
class SimulationRunMetadata:
    run_id: str
    dataset_id: str
    started_at: datetime
    completed_at: datetime
    target_commit_id: str

@dataclass(frozen=True)
class SimulationReport:
    metadata: SimulationRunMetadata
    strategy_identities: tuple[StrategyIdentity, ...]
    race_results: tuple[SimulationResult, ...]
    strategy_summaries: Mapping[str, SimulationSummary]
    official_roi_valid: bool
    validation_errors: tuple[SimulationValidationError, ...]
```

`SimulationRunContext` は入力専用であり、`run_id`、`dataset_id`、`started_at`、`target_commit_id`を持つ。`completed_at`、stake、対応券種、対象期間は現行正式モデルのフィールドではない。`SimulationRunMetadata` は実行完了後の`completed_at`を追加する。`SimulationReport` は全Strategy・全レースの明細を保持する設計上の出力コンテナである。

## Simulatorの入出力と既存パイプライン連携

### 実行境界（第4C-2b1 / 2b2）

`Simulator` は一つの `StrategyIdentity` と、一レースを最終 `SimulationResult` に変換する注入済みexecutorを保持する。`run()` は全 `SimulationRaceInput` を実行前に検証した後、入力順のままexecutorを各レースに一回だけ呼び、全結果を `_build_simulation_summary()` へ一回だけ渡す。これにより、Provider・Repository・外部I/Oを `Simulator` へ直接持ち込まない。

```python
class RaceSimulationExecutor(Protocol):
    def __call__(
        self,
        *,
        race_input: SimulationRaceInput,
    ) -> SimulationResult:
        ...


class Simulator:
    def __init__(
        self,
        *,
        strategy_identity: StrategyIdentity,
        race_executor: RaceSimulationExecutor,
    ) -> None:
        ...
```

constructorは`StrategyIdentity`を再生成・分解・補正せず、同一のimmutable objectを保持する。`race_executor`はcallableであることだけをFail Closedで検証し、signature検査・試験実行・wrapper化を行わない。`run()`はexecutorを各`SimulationRaceInput`に一回だけ呼び、保持した`strategy_id`、`strategy_name`、`strategy_config_hash`を`_build_simulation_summary()`へ明示的に渡す。外部取得・保存・CLI出力はさらに上位層の責務とする。

## Provider接続境界（第4C-2c1）

### Simulatorは変更しない

Providerを`Simulator`へ直接注入しない。`Simulator.__init__`、`Simulator.run()`、`RaceSimulationExecutor`、`SimulationRaceInput`、`SimulationResult`、`SimulationSummary`、`models.py`の契約は変更しない。`Simulator`は注入された`RaceSimulationExecutor`だけを認識し、Provider・Repository・SQLite・DB・HTTP・network・retry・logging・現在時刻取得へ依存しない。

### 既存Providerは変換Providerである

既存の`RaceResultProvider`、`OddsSnapshotProvider`、`PayoutProvider`は、Rawモデル、`ProviderContext`、`RaceEntryUniverse`からRepository境界モデルを構築する変換Providerである。取得・DB照会・外部I/Oを行うProviderではない。

```text
Rawデータ
  → 変換Provider
  → PersistedRaceResult / OddsSnapshotBatch / PayoutPublication
```

これらのProviderへ、DB接続、Repository実装、SQLite、HTTP、network、retry、logging、現在時刻取得を追加しない。Phase 4C-2cの最小接続対象は確定結果と払戻であり、`OddsSnapshotProvider`は予測入力・EVの後続責務としてこのadapterへ追加しない。

### 現行型・Result builderの実装可能性

次表は、Provider接続executorが必要とする情報を現行型が実際に保持するかを示す。存在しないフィールドを補完・推測しない。

| 型 | 実在フィールドと利用可能な情報 | Provider接続上の不足または注意点 |
| --- | --- | --- |
| `SimulationRaceInput` | `race_id`、`scheduled_start_at`、`information_cutoff`、`pipeline_input`、`input_snapshot_audit` | 購入内容、購入券種、`strategy_id`を保持しない。`pipeline_input`から`SimulationBet`を復元する契約も存在しない。 |
| `SimulationBet` | `race_id`、`strategy_id`、`bet_type`、正規化済み`race_entry_ids`、`stake`、`recommendation_rank`、`placed_at_cutoff` | 購入券種の正規情報源になれるが、`SimulationRaceInput`から取得できない。 |
| `RawRaceResult` | `declared_status`、`finalized_at`、`entries` | `race_id`、監査時刻、sourceを持たない。`ProviderContext`と`RaceEntryUniverse`が必要。 |
| `RawPayoutPublication` | `bet_type`、`finalized_at`、`entries`、3つの完全性フラグ | 一券種一publicationであり、`race_id`、監査時刻、sourceを持たない。券種ごとの`ProviderContext`と`RaceEntryUniverse`が必要。 |
| `ProviderContext` | `race_id`、`observed_at`、`source`、`source_url`、`captured_at`、`information_cutoff`、任意の`bet_type` | 結果用と券種ごとの払戻用を区別して保持する必要がある。ここでの`information_cutoff`はRaw取得・変換時のSource境界であり、`SimulationRaceInput.information_cutoff`とは別の時点である。 |
| `RaceEntryUniverse` | `race_id`、active/excluded/cancelledのentry ID集合、`horse_no_to_race_entry_id` | 結果・払戻の両Providerへ共通に渡せる。`race_id`は入力と一致しなければならない。 |
| `PersistedRaceResult` | `race_id`、`result_status`、`finalized_at`、`observed_at`、`entries` | COMPLETEなら`finalized_at`が必須。結果確定時刻の正式な取得元になる。 |
| `PayoutPublication` | `race_id`、`bet_type`、`finalized_at`、`observed_at`、`is_complete`、`entries` | COMPLETEなら`finalized_at`が必須。必要券種ごとの払戻確定時刻の正式な取得元になる。 |
| `ProviderBuildResult` | `value`と`CompletenessResult` | 結果・払戻を変換した後、値と完全性を一組で保持できる。 |
| `CompletenessResult` | `status`、件数、missing/unexpected/duplicate keys、reasons | `COMPLETE`、`INCOMPLETE`、`INVALID`、`UNSUPPORTED`をResult builderへ渡す事実になる。 |
| `_build_simulation_result_for_race(...)` | `race_id`、`strategy_id`、`bets`、`publications_by_bet_type`、`settled_at`、完全性status、結果status、払戻status、欠損券種、結果欠損、`error_reason` | `RaceSettlementData`とexecutorが供給する値で構成する。`SimulationRaceInput`単独から購入内容やstrategy identityは構成できない。 |

したがって、Raw Provider経路の`ProviderBackedRaceSimulationExecutor`は`RaceSettlementData`を供給するSourceと組み合わせて使用する。一方、既存Repositoryが返すPersistedモデルだけから同bundleを構成することはできない。購入内容、Raw監査情報、Universe、時点選択の取得境界はRepository経路で別途設計する。

### Source戻り値bundleとRaceSettlementSource

購入内容とRawデータを別々に取得すると、同一レース・同一時点・同一購入計画であることを保証できない。このため、新規のimmutable bundleを導入する。仮称は`RaceSettlementData`、配置候補は新規の`scripts/simulation/settlement.py`である。既存の変換Provider契約を保つため、`providers/interfaces.py`には追加しない。

```python
@dataclass(frozen=True)
class RaceSettlementData:
    race_id: int
    bets: tuple[SimulationBet, ...]
    raw_race_result: RawRaceResult | None
    race_result_context: ProviderContext | None
    raw_payout_publications_by_bet_type: Mapping[str, RawPayoutPublication]
    payout_contexts_by_bet_type: Mapping[str, ProviderContext]
    universe: RaceEntryUniverse
```

bundleはtupleと不変Mappingへfreezeし、Repository、DB接続、SQLite実装、外部clientを保持しない。validation責務は次のとおりとする。

- `race_id`、`universe.race_id`、呼出し元`SimulationRaceInput.race_id`が一致する。
- `bets`の全要素は`SimulationBet`であり、各`race_id`がbundleの`race_id`と一致する。
- `raw_race_result`と`race_result_context`は両方存在するか両方`None`である。存在時のcontextは対象`race_id`と一致する。
- 払戻Mappingのkeyは正規化済み券種で、各`RawPayoutPublication.bet_type`と一致する。各券種に対応する`ProviderContext`が存在し、対象`race_id`と一致する。contextの`bet_type`が存在する場合はMapping keyと一致する。
- bundle内の結果・払戻Contextは同じRaw取得・変換時点の`information_cutoff`を共有する。ただし、その値を`SimulationRaceInput.information_cutoff`と一致させてはならない。
- 払戻Mappingに存在しない購入券種は欠損として表し、空の偽publicationや推測データで補完しない。

`RaceSettlementSource`の次フェーズ実装候補は以下である。

```python
class RaceSettlementSource(Protocol):
    def load_settlement_data(
        self,
        *,
        race_input: SimulationRaceInput,
    ) -> RaceSettlementData:
        ...
```

SourceはRaw結果、券種単位のRaw払戻、各ProviderContext、Universe、購入内容を同一レース・同一時点のデータとして供給する取得境界である。DB取得・外部取得の実装を持つことは許容するが、変換Providerへその依存を移さない。

### ProviderBackedRaceSimulationExecutorのAPI

`SimulationRaceInput`には`strategy_id`がないため、NO_BETを含む全Result builder呼出しに必要なidentityをexecutor自身が保持する。composition rootは、`Simulator`とexecutorへ同一の`StrategyIdentity` objectを渡す。

```python
class ProviderBackedRaceSimulationExecutor:
    def __init__(
        self,
        *,
        strategy_identity: StrategyIdentity,
        settlement_source: RaceSettlementSource,
        race_result_provider: RaceResultProvider,
        payout_provider: PayoutProvider,
    ) -> None:
        ...

    def __call__(
        self,
        *,
        race_input: SimulationRaceInput,
    ) -> SimulationResult:
        ...
```

Result builderは追加注入しない。`_build_simulation_result_for_race(...)`は現在の正式な一レース組立境界であり、module-level helperを直接一回だけ呼ぶ。Callable注入は、既存のprivate helperを新たな公開契約へ昇格させ、責務とテスト境界を不必要に広げるため採用しない。

### 購入券種と購入なしの処理

購入対象は`RaceSettlementData.bets`である。`SimulationRaceInput`単独からは取得できない。必要券種は、入力順を保つ最初の出現順で次のように抽出する。

```text
tuple(dict.fromkeys(bet.bet_type for bet in bets))
```

`SimulationBet`は正規化済みの対応券種しか保持できない。Sourceが`SimulationBet`以外、対象外券種、別race、またはexecutorの`strategy_identity.strategy_id`と異なるbetを返した場合はfail-closedで例外を伝播し、Providerを呼ばない。券種の順序はpublication Mappingの意味には影響しないが、Provider呼出しと監査を決定的にするため最初の出現順を維持する。

`bets == ()`は購入なしである。ただし、購入内容はSource bundleからしか得られないため、まずSourceを一回呼ぶ。空であると確定した後は結果・払戻Providerを呼ばず、`_build_simulation_result_for_race(...)`へ空betsを一回だけ渡してNO_BETを生成する。Source呼出し自体を省略する契約にはしない。

現行helperはNO_BET分岐で`settled_at`を使わない一方、引数型は非optionalな`datetime`である。意味のない時刻を渡さないため、実装前にhelperの`settled_at`を`datetime | None`へ変更し、SETTLED分岐だけでtimezone-awareな値を必須検証する最小修正が必要である。

### 完全性状態と現行Result builderの制約

executorはSource／Provider例外をResultへ変換せず、そのまま伝播する。partial settlementは常に禁止する。Providerが正常に`ProviderBuildResult`を返した場合の現行Result builderの実際の挙動は次表のとおりである。

| 条件 | Result builderを呼ぶか | 非精算Resultへ変換 | 例外を伝播 | 部分精算 | 現行契約上の結論 |
| --- | --- | --- | --- | --- | --- |
| result COMPLETE、必要payout全てCOMPLETE | 呼ぶ | しない | 評価・時刻が正常ならしない | 不可 | SETTLED可能。 |
| result INCOMPLETE | 条件付きで呼ぶ | 評価成功時のみUNSETTLED | 必要publication欠損・評価不能時はする | 不可 | 非精算判定より評価が先のため、確実には表現不能。 |
| result INVALID | 条件付きで呼ぶ | 評価成功時のみERROR | 評価不能時はする | 不可 | 同上。 |
| result UNSUPPORTED | 条件付きで呼ぶ | 評価成功時のみUNSUPPORTED | 評価不能時はする | 不可 | 同上。 |
| 必要payoutがINCOMPLETE | 条件付きで呼ぶ | 全betが評価可能な場合のみUNSETTLED | 未一致betは評価例外を伝播 | 不可 | 不完全払戻の不的中と欠損を安全に区別できない。 |
| 必要payoutがINVALID | 条件付きで呼ぶ | 評価成功時のみERROR | 評価不能時はする | 不可 | 同上。 |
| 必要payoutがUNSUPPORTED | 条件付きで呼ぶ | 評価成功時のみUNSUPPORTED | 購入selectionがunsupported recordに一致すると評価例外を伝播 | 不可 | 同上。 |
| 必要な払戻publicationがない | 呼ぶと評価前に失敗 | できない | する | 不可 | publication key集合の完全一致を評価helperが要求するため、現行モデルではUNSETTLEDを表現不能。 |
| 未購入券種だけの払戻がない | 呼ぶ | しない | しない | 不可 | 必要券種集合に含めないため影響しない。 |
| Source例外 | 呼ばない | しない | する | 不可 | 例外をそのまま伝播。 |
| Provider例外 | 呼ばない | しない | する | 不可 | 例外をそのまま伝播。 |
| Result builder例外 | 呼んだ後に返さない | しない | する | 不可 | 例外をそのまま伝播。 |

`_build_simulation_result_for_race(...)`は、空betsでNO_BETを返し、それ以外は非精算statusを評価より先に判定し、SETTLED時だけ`_evaluate_simulation_race_bets(...)`を呼ぶ。`settled_at`は`datetime | None`であり、SETTLED分岐だけがtimezone-awareな値を必須とする。この前提修正はPhase 4C-2c2の実装前に完了している。

### `settled_at`の実装可能性

正式な確定時刻は変換後の値から取得する。

- 結果: `PersistedRaceResult.finalized_at`
- 必要券種の払戻: 各`PayoutPublication.finalized_at`

COMPLETEな`PersistedRaceResult`とCOMPLETEな`PayoutPublication`は、いずれも`finalized_at`を必須とする。したがって、全ての必要情報がCOMPLETEであるSETTLED候補では次を決定できる。

```text
max(
    persisted_race_result.finalized_at,
    required_payout_publication.finalized_at for each required bet type,
)
```

一つでも欠ける場合は`settled_at`を決定できない。`datetime.now()`、`observed_at`、`captured_at`、`information_cutoff`で代用しない。欠損時刻の追加先はSourceではなく、既に正式フィールドを持つ変換後の`PersistedRaceResult`／`PayoutPublication`を構築するProvider入力・変換境界である。

### Result builder引数の構成

前提フェーズ後、`_build_simulation_result_for_race(...)`の各引数は次の実在値から構成する。

| Result builder引数 | 構成元 |
| --- | --- |
| `race_id` | `race_input.race_id`。bundleの`race_id`およびUniverseの`race_id`と一致を確認する。 |
| `strategy_id` | executorへ注入された`strategy_identity.strategy_id`。bundleの全betとも一致を確認する。 |
| `bets` | `RaceSettlementData.bets`。 |
| `publications_by_bet_type` | 正常に変換できた必要券種の各`ProviderBuildResult[PayoutPublication].value`。欠損券種を偽publicationで補完しない。 |
| `settled_at` | SETTLED候補でのみ、結果と必要払戻の`finalized_at`の最大値。その他は`None`。 |
| `completeness_statuses` | 存在する結果・必要払戻の各`ProviderBuildResult.completeness.status`。 |
| `race_result_status` | 結果が存在する場合は`ProviderBuildResult[PersistedRaceResult].value.result_status`、結果未取得時は`None`。 |
| `payout_statuses` | 必要券種の各変換済み`PayoutPublication.entries`に含まれる`PayoutRecord.payout_status`。 |
| `missing_payout_bet_types` | 必要券種のうち、Raw publicationまたは対応contextが存在しない券種。 |
| `missing_race_result` | `raw_race_result`と`race_result_context`がともに`None`であること。 |
| `error_reason` | Source／Provider／builder例外は伝播する方針のため、通常経路では常に`None`。 |

この対応表のうち、空または欠損の`publications_by_bet_type`を安全に受け入れるためには、前節で記したResult builderの判定順変更が必要である。

### 1レースの正式処理フロー

購入ありの場合は、次の順序とする。

```text
race_input受付
→ RaceSettlementSourceを一回呼ぶ
→ RaceSettlementDataとrace_input、strategy_identityを検証
→ betsから必要券種を最初の出現順で決定
→ RaceResultProviderで結果を一回変換（結果Rawが存在する場合）
→ 必要券種ごとにPayoutProviderで払戻を一回変換（Rawが存在する場合）
→ publication Mapping、完全性status、結果status、払戻status、欠損券種を構成
→ SETTLED候補だけでsettled_atを決定
→ _build_simulation_result_for_race(...)を一回呼ぶ
→ SimulationResult返却
```

購入なしの場合は次の順序とする。

```text
race_input受付
→ RaceSettlementSourceを一回呼ぶ
→ RaceSettlementDataとstrategy_identityを検証
→ betsが空であることを確認
→ ResultProviderとPayoutProviderを呼ばない
→ _build_simulation_result_for_race(...)を一回呼ぶ
→ NO_BET SimulationResult返却
```

この購入なしフローには、上記の`settled_at: datetime | None`への最小変更が前提となる。

### 実装可能性の結論

Raw Provider経路の契約と`ProviderBackedRaceSimulationExecutor`は実装済みである。残る実装可能性の課題は、具体的なRaw SourceまたはRepositoryからのPersisted経路が購入bet・結果・払戻を安全に供給する境界である。詳細は次節のPrediction cutoffとSettlement pathで定義する。Odds、Summary builder、`Simulator.run()`、`models.py`の契約はこの境界設計では変更しない。

## Prediction cutoffとSettlement path（Phase 4C-2d1a）

この節は、上記Provider接続境界における時点の意味と、Raw Provider経路／Persisted Repository経路を正式に分離する。`SimulationRaceInput.information_cutoff`と`ProviderContext.information_cutoff`を同一視する従来の記述は、この節の決定で置き換える。

### 予測cutoffと精算cutoffは別境界である

`SimulationRaceInput.information_cutoff`は予測・購入判断の情報上限である。能力、展開、騎手、馬場・コース、odds snapshot、bet生成、strategy判断には、この時点以後の情報を使わない。

確定着順、結果status、払戻、結果の`finalized_at`、払戻の`finalized_at`はレース終了後の精算事実であり、予測cutoffで制限しない。したがって、精算に用いる値の`observed_at > SimulationRaceInput.information_cutoff`は通常の正常状態である。未来情報遮断とは、精算事実を予測・bet生成へ逆流させないことであり、精算処理がレース後の確定事実を使うことを禁止する意味ではない。

`ProviderContext.information_cutoff`は、Raw結果／Raw払戻を取得して変換したSource側の情報上限である。ProviderContext自身の`observed_at <= information_cutoff`および`captured_at <= information_cutoff`という契約は維持するが、そのcutoffは通常レース終了後であり、`SimulationRaceInput.information_cutoff`との一致を要求しない。

このため、次の整合性は維持する。

- bundle、Provider出力、`SimulationRaceInput`の`race_id`整合性。
- bundleのbetとexecutorの`StrategyIdentity.strategy_id`整合性。
- bundle内部の結果・払戻ProviderContext同士のRaw取得・変換境界としての整合性。
- Provider出力の型、監査時刻、券種、確定時刻の整合性。

一方、`ProviderBackedRaceSimulationExecutor`が現在行う、Provider Context cutoffまたはProvider出力の`observed_at`を`race_input.information_cutoff`と比較して拒否する検証は正式設計と矛盾する。次のコードフェーズで廃止する。精算情報が予測cutoffより後でも拒否せず、ProviderContext自身の時点契約だけを検証する。

### Raw Provider経路

Raw Provider経路は、取得直後の監査可能なRawデータを既存Providerで一度だけ変換する経路である。

```text
RawRaceResult / RawPayoutPublication
  → RaceResultProvider / PayoutProvider
  → PersistedRaceResult / PayoutPublication
  → SimulationResult
```

使用クラスは`ProviderBackedRaceSimulationExecutor`である。この経路はRaw ingestion接続、Raw fixtureを用いる統合試験、Provider変換契約を含む精算に使用する。RawからPersistedへの変換・完全性判定はこの経路で一度だけ実行する。

### Persisted Repository経路

Repositoryから読み出した正規化済みデータは、Rawへ逆変換しない別経路で精算する。

```text
PersistedRaceResult / PayoutPublication
  → SimulationResult
```

この経路では、PersistedモデルからRawモデルへの逆変換、RaceResultProvider／PayoutProviderの再実行、完全性判定の二重実行、原文statusの推測復元、欠落したRaw監査情報の補完を行わない。これらはRaw監査情報を失わせ、変換責務を二重化するため禁止する。

### Persisted settlement bundleとSource

Persisted経路のimmutable bundle候補は`settlement.py`に配置する。実在型のimport元は`SimulationBet`、`SimulationRaceInput`、`StrategyIdentity`が`simulation.models`、`PersistedRaceResult`と`PayoutPublication`が`simulation.repositories.interfaces`である。

```python
@dataclass(frozen=True, slots=True)
class PersistedRaceSettlementData:
    race_id: int
    bets: tuple[SimulationBet, ...]
    race_result: PersistedRaceResult | None
    payout_publications_by_bet_type: Mapping[str, PayoutPublication]
```

このbundleはRawモデル、ProviderContext、RaceEntryUniverse、Provider、Repository、DB／SQLite connection、logger、HTTP client、現在時刻生成関数を保持しない。`bets`はtupleへ固定し、Mappingは防御的コピー後のread-only Mappingへfreezeするため、元のMapping変更の影響を受けない。

validation候補は以下とする。

- `race_id`は正の非bool int。
- 全betは`SimulationBet`であり、各`bet.race_id`はbundleの`race_id`と一致する。
- `race_result`が存在するとき、その`race_id`はbundleの`race_id`と一致する。
- 払戻Mappingの全valueは`PayoutPublication`であり、各`race_id`はbundleの`race_id`と一致する。
- Mapping keyは各`PayoutPublication.bet_type`と一致する。

StrategyIdentityとの一致はbundleではなくexecutorが検証する。

```python
class PersistedRaceSettlementSource(Protocol):
    def load_settlement_data(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> PersistedRaceSettlementData:
        ...
```

このProtocolはrace inputとstrategy identityをkeyword-onlyで受ける。対象strategyのbetsと、Repositoryから読んだ正規化済み結果・必要払戻をbundleとして供給する。Rawへ戻さず、Providerを呼ばず、Repository／DBの具体実装をProtocolへ露出させない。既存の`RaceSettlementSource`はRaw Provider経路専用として維持し、名前を共有しない。

### 購入betの取得境界

既存Repositoryには`SimulationBet`取得契約も永続化schemaもない。最小の論理境界は次とする。

```python
class SimulationBetSource(Protocol):
    def load_bets(
        self,
        *,
        race_input: SimulationRaceInput,
        strategy_identity: StrategyIdentity,
    ) -> tuple[SimulationBet, ...]:
        ...
```

このSourceはraceとstrategyを限定し、stake、selection、bet typeを完全に復元し、正式な購入順を維持する。別race／別strategyのbetを返さず、prediction cutoff以後に新規生成されたbetを混入させない。

betをDBへ永続化するか、上位層から実行時に供給するか、prediction pipelineの出力を保持するか、購入順をどのフィールドで固定するか、bet生成時刻またはcutoffをどこに保存するかは未確定である。この節ではschemaを確定・追加しない。

### Persisted executor

Persisted経路の推奨名は`PersistedRaceSimulationExecutor`とする。`RepositoryBackedRaceSimulationExecutor`よりも、具体的なSQLite／Repository実装をexecutorから隔離し、入力がPersisted境界モデルである事実を明確に表せるためである。

```python
class PersistedRaceSimulationExecutor:
    def __init__(
        self,
        *,
        strategy_identity: StrategyIdentity,
        settlement_source: PersistedRaceSettlementSource,
    ) -> None:
        ...

    def __call__(
        self,
        *,
        race_input: SimulationRaceInput,
    ) -> SimulationResult:
        ...
```

このexecutorはSourceを一回呼び、race・strategy整合性を検証し、betsから必要券種を抽出する。Persisted結果・必要払戻を既存の`_build_simulation_result_for_race(...)`へ最大一回だけ渡し、SETTLED候補では結果と必要払戻の`finalized_at`の最大値を`settled_at`とする。Provider呼出し、Raw再構成、SQL、DB接続、Summary集計、atomic evaluatorの直接呼出し、個別Result builderの直接呼出しを行わない。

### Final settlement方針と再現性

Ver0.8のRepository経路は最終確定情報による精算を対象とする。

- `SimulationRaceInput.information_cutoff`はbet生成までにだけ使用する。
- 精算は最終の確定結果・確定払戻を使用し、予測cutoffより後の確定は正常である。
- SETTLEDでは結果および必要払戻の`finalized_at`を必須とする。
- 欠損・非確定statusはfail-closedで非精算とし、必要券種の払戻が欠ける場合は非精算とする。
- 未購入券種の払戻は不要であり、結果・払戻を予測処理へ戻さない。

結果revision／払戻revisionの時点再現、レース終了後何分で精算可能だったかの再現、correction前の結果による精算、settlement as-ofによるtime travelは今回の対象外である。現行DB snapshotが変われば再計算結果も変わり得るため、厳密な再現性にはDB snapshotまたはversion管理が必要になる。

### Repository境界の不足と責務分担

現時点で必須なのは`SimulationBetSource`、Persisted settlement bundle／Source、Raw Provider経路をRepositoryへ接続する場合の正式なRaceEntryUniverse取得境界である。Repository経路では、既存の`get_race_result(race_id)`の最終情報取得としての利用可否、券種ごとの最新complete payout取得、bet取得、strategy identityによる絞り込みを設計する。後続の検討対象はresult revision、`observed_at_lte`結果lookup、Raw監査情報保存、cancelled／excluded entry情報、source_url／captured_at保存である。

| 層 | 責務 |
| --- | --- |
| `SimulationBetSource` | race・strategy別betの取得 |
| Repository | SQLとPersistedモデル復元 |
| `PersistedRaceSettlementSource` | bet・結果・払戻を1レースbundleへ構成 |
| `PersistedRaceSimulationExecutor` | 必要券種、非精算判定、`settled_at`、Result builder接続 |
| Raw Provider | RawからPersistedモデルへの変換 |
| `ProviderBackedRaceSimulationExecutor` | Raw Provider経路のオーケストレーション |
| `Simulator` | 複数raceの順序実行とSummary一回集計 |

### 次フェーズの依存順

```text
Phase 4C-2d1b
ProviderBackedRaceSimulationExecutorのcutoff整合性修正

Phase 4C-2d1c
PersistedRaceSettlementData／PersistedRaceSettlementSource契約追加

Phase 4C-2d1d
SimulationBetSource契約追加

Phase 4C-2d1e
PersistedRaceSimulationExecutor実装

Phase 4C-2d3
必要なbet永続化／Repository境界

Phase 4C-2d2
Repository-backed Sourceの具体設計・実装

Phase 4C-2e
composition root／CLI接続
```

`PersistedRaceSimulationExecutor`はdummy Sourceを用いて`Phase 4C-2d1e`で実装・検証できる。一方、実際のRepository-backed Sourceはbetを取得できなければ構成できないため、当初案の2d2より先に2d3を置く。

### Simulation bet plan identity／変換境界（Phase 4C-2d3b0）

#### bet plan は run 単位の immutable snapshot

永続化する単位は独立したbetの集合ではなく、**一つのsimulation run・一つのrace・一つのstrategy・一つのprediction cutoff**に対応する購入計画snapshotである。正式な概念名を`SimulationBetPlanSnapshot`とする。

snapshotはinsert-onlyであり、保存後に置換・上書きしない。同じrace・strategy・prediction cutoffであっても、異なるrunで生成されたplanは別snapshotとして保存する。DB内部のsurrogate primary keyは許容するが、domain上のidentityを置き換えない。

現行の`SimulationRunContext`は次の正式フィールドを持つ。

```python
@dataclass(frozen=True)
class SimulationRunContext:
    run_id: str
    dataset_id: str
    started_at: datetime
    target_commit_id: str
```

`run_id`、`dataset_id`、`target_commit_id`は非空、`started_at`はtimezone-awareである。bet plan identityへ必須で入るrun情報は`run_id`であり、dataset、commit、開始時刻はrunの来歴として`SimulationRunContext`に保持する。新しいrun ID生成ロジックはこの境界で追加しない。

#### `SimulationBetPlanIdentity`

後続実装で追加するdomain contractは次とする。

```python
@dataclass(frozen=True, slots=True)
class SimulationBetPlanIdentity:
    run_id: str
    race_id: int
    strategy_id: str
    strategy_config_hash: str
    information_cutoff: datetime
```

validationは以下を満たす。

- `run_id`と`strategy_id`は非空の`str`。
- `race_id`は正の非bool `int`。
- `strategy_config_hash`は既存`StrategyIdentity.strategy_config_hash`と同じ、64文字の小文字SHA-256 digest。
- `information_cutoff`はtimezone-aware `datetime`。
- 呼出し側は`StrategyIdentity.strategy_id`と`strategy_config_hash`、`SimulationRaceInput.race_id`と`information_cutoff`からidentityを構成し、推測・補正しない。

後続migrationでは、この五つの複合identityにunique constraintを置く。同一run内で同一race・strategy・設定・cutoffのplanを二つ保存することは許可しない。

#### Source への run identity 供給

既存Protocolの`load_bets()`および`load_settlement_data()`の引数にrun IDを追加しない。Repository-backed Sourceをrun単位で構築し、constructorで固定する。

```python
class RepositoryBackedSimulationBetSource:
    def __init__(
        self,
        *,
        run_context: SimulationRunContext,
        bet_repository: SimulationBetRepository,
    ) -> None:
        ...
```

`run_id`だけではなく`SimulationRunContext`全体をconstructorへ注入する案を採用する。既存の不変・検証済みrun境界を保持し、Sourceがrun IDを再生成せず、将来のdataset/commit監査にも同じobjectを使えるためである。`load_bets(race_input=..., strategy_identity=...)`は、固定された`run_context.run_id`と引数のrace・strategy・cutoffから`SimulationBetPlanIdentity`を一意に構成する。

`PersistedRaceSettlementSource`の具体実装も、同一`run_context`で構築済みの`SimulationBetSource`を合成するか、同じ`run_context`をconstructor注入する。`Simulator.run()`、`RaceSimulationExecutor`、既存Source Protocolのsignatureは変更しない。

#### `SimulationBetPlanSnapshot` と空plan

```python
@dataclass(frozen=True, slots=True)
class SimulationBetPlanSnapshot:
    identity: SimulationBetPlanIdentity
    bets: tuple[SimulationBet, ...]
```

snapshotは次を検証する。

- `identity`は`SimulationBetPlanIdentity`。
- `bets`は防御的にtuple化し、外部の元Sequence変更の影響を受けない。
- 空tupleを許可する。
- 各betの`race_id`、`strategy_id`、`placed_at_cutoff`はidentityの`race_id`、`strategy_id`、`information_cutoff`と完全一致する。
- plan内のbet identity `(bet_type, canonical race_entry_ids)` は重複不可。
- frozenおよびslotsとし、betの順序そのものをsnapshotの正式なpurchase orderとする。

`bets == ()`は、対象run・race・strategy・cutoffについて購入計画が正式に確定したが、購入betが0件だったことを表す。これはplan未生成、未保存、取得失敗とは異なる。後続schemaはbet子行が0件でもplan headerを保存しなければならない。

#### prediction cutoff、recommendation rank、purchase order

`SimulationBet.placed_at_cutoff`は実時計の購入時刻ではなく、購入判断で使用した情報上限である。snapshotでは必ず次を満たす。

```text
bet.placed_at_cutoff == snapshot.identity.information_cutoff
```

これにより、異なるprediction cutoffのplanを区別し、後から生成されたbetの混入を拒否する。保存時刻や`datetime.now()`で代用しない。実際の購入実行時刻が必要になった場合は、別フィールド・別境界として設計する。

`recommendation_rank`は候補評価順位であり、purchase orderではない。正式なpurchase orderは、`BetStrategy`が確定した`BetPlan.recommendations`のtuple順を先頭から列挙した0-based index (`0, 1, 2, ...`) とする。後続schemaではplan子行に`purchase_order INTEGER NOT NULL CHECK(purchase_order >= 0)`を保存し、plan内unique constraintと読取時の`ORDER BY purchase_order ASC`で順序を再現する。surrogate bet IDをtie-breakerに使わない。

同じplan内ではstake、rank、purchase orderが異なっても`(bet_type, canonical race_entry_ids)`が同じbetを拒否する。別plan・別run間では同一identityを許可する。この方針は既存`SimulationResult`と`RuleBasedBetStrategy`の重複排除契約に合わせる。

#### `BetPlan` から snapshot への変換

実在するpredictionモデルは以下である。

```python
@dataclass(frozen=True)
class BetPlan:
    strategy_name: str
    recommendations: tuple[BetRecommendation, ...]
    candidate_count: int

@dataclass(frozen=True)
class BetRecommendation:
    rank: int
    bet_type: str
    horse_ids: tuple[int, ...]
    estimated_probability: float
    expected_value: float | None
    combination_score: float | None
    prediction_score: float
```

`BetPlan`にも`BetRecommendation`にもstake、amount、purchase order、race ID、strategy ID、prediction cutoffは存在しない。`StrategyConfig`および`SimulationRunContext`にもstake allocationの正式フィールドはない。したがって、stakeを均等配分・100円固定・既定値から推測することは禁止する。

最終的な純粋変換は`SimulationBetPlanBuilder`を推奨する。BuilderはDB、Repository、Provider、現在時刻、strategy再実行、recommendationの再ソートへ依存せず、plan identity、確定済みstake allocation、race entry selection resolverを受けてsnapshotを返す。stake allocationの正式契約が未確定であるため、`build(...)`の完全signatureはこの時点では確定しない。少なくとも以下の責務を持つ。

```text
BetPlanのtuple順を保持
→ 各recommendationのhorse_idsをresolve
→ 確定済みallocationからstakeを取得
→ SimulationBetを構築
→ plan内重複を拒否
→ SimulationBetPlanSnapshotを返す
```

`BetStakeAllocator`または`BetAllocationPlan`の設計が、変換実装の前提フェーズとして必要である。allocationはrecommendationごとのstakeを損失なく表し、最終`BetPlan`のtuple順との対応を明示しなければならない。

#### horse IDs から race entry IDs への変換

`BetRecommendation.horse_ids`と`SimulationBet.race_entry_ids`は別境界である。現在のCLI実装では両者が`horses.id`由来に見えるが、Builderが暗黙に同一IDとして扱ってはならない。

```python
class RaceEntrySelectionResolver(Protocol):
    def resolve_race_entry_ids(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> tuple[int, ...]:
        ...
```

resolverは指定race内でhorse IDをrace entry IDへ変換し、別race、欠損ID、重複IDを拒否する。Builderはrecommendation由来の順序をそのままresolverへ渡し、券種別canonicalizationは最終的な`SimulationBet` constructorへ一元化する。Repository/DB依存はresolverの具体実装に閉じ込め、純粋Builderへ直接埋め込まない。上位層で変換済み`BetPlan`を生成する案は既存`BetPlan`の型を変える必要があるため、今回の最小方針には採用しない。

#### 将来の Repository API

`SimulationBetRepository`は個別betではなくplan snapshotを保存・取得する。

```python
class SimulationBetRepository(Protocol):
    def save_plan(
        self,
        *,
        snapshot: SimulationBetPlanSnapshot,
    ) -> SimulationBetPlanSnapshot:
        ...

    def get_plan(
        self,
        *,
        identity: SimulationBetPlanIdentity,
    ) -> SimulationBetPlanSnapshot | None:
        ...
```

Repositoryはidentityを生成しない。insert-onlyで同一identityの再保存を拒否し、空planも保存する。読取時はpurchase orderを維持し、DB行をdomain constructor validationへ通して復元する。Repository読取時刻をprediction cutoffとして使用しない。

#### Phase 4C-2d3b の進行判定と分割

**Phase 4C-2d3b1の前に追加設計が必要**である。identity、run供給、空plan、purchase order、`placed_at_cutoff`不変条件、selection resolver、変換責務は確定したが、recommendationごとのstakeの正式取得元が存在しない。

次の順序とする。

```text
Phase 4C-2d3b0a
BetStakeAllocator / BetAllocationPlan の入力・出力・順序対応を設計する。

Phase 4C-2d3b0a1
BetStakeBudget、BetAllocationPlan、BetStakeAllocator、allocation policy設定の
domain / Protocol契約を追加する。

Phase 4C-2d3b0a2
最初の具体的BetStakeAllocator policyを設計・実装する。

Phase 4C-2d3b0b
SimulationBetPlanIdentity、SimulationBetPlanSnapshot、
RaceEntrySelectionResolver のdomain / Protocol契約を追加する。

Phase 4C-2d3b0c
確定済みallocationを使う SimulationBetPlanBuilder を実装する。

Phase 4C-2d3b1
bet plan schema / migration を追加する。

Phase 4C-2d3b2
SimulationBetRepository と SQLite実装を追加する。

Phase 4C-2d3b3
Repository-backed SimulationBetSource を実装する。

Phase 4C-2d3b4
PredictionPipeline の最終BetPlanをsnapshotとして保存する上位接続を実装する。
```

stake allocationの入力・境界は直後のPhase 4C-2d3b0aで確定する。schema、Repository、Sourceの実装は、同節で定めるbudget、allocation policy設定、run contextのcomposition root供給を後続契約として実装するまで開始しない。

#### BetStakeAllocator／BetAllocationPlan（Phase 4C-2d3b0a）

##### 既存のbudget・stake境界

現行の`BetPlan`は`strategy_name`、順序付き`recommendations`、`candidate_count`だけを持ち、`BetRecommendation`は`rank`、`bet_type`、`horse_ids`、確率・score・expected value関連値だけを持つ。stake、amount、budget、purchase orderは存在しない。`RuleBasedBetStrategy`と`StrategyConfig`も購入対象と`max_bet_count`を決めるだけで、資金配分を持たない。

prediction CLIには`--max-bets`があるが、これは購入点数上限でありbudgetやstakeではない。設定JSON、race単位budget、stake allocation処理は存在しない。旧`models.Bet.amount`はsimulation planや`BetPlan`に接続されない別モデルであり、allocationの入力に使用しない。

##### stake allocation の責務と処理順

stake allocationは`BetStrategy`の後、race entry selection解決と`SimulationBet`構築の前に行う。

```text
PredictionPipeline
→ BetGenerator
→ BetStrategy
→ 最終 BetPlan
→ BetStakeAllocator
→ BetAllocationPlan
→ RaceEntrySelectionResolver
→ SimulationBetPlanBuilder
→ SimulationBetPlanSnapshot
```

| 層 | 責務 |
| --- | --- |
| `BetStrategy` | 最終recommendation集合と順序を確定する。 |
| `BetStakeAllocator` | 既存recommendationごとのstakeを配分し、budgetを検証する。 |
| `BetAllocationPlan` | allocation結果をimmutableに表す。 |
| `RaceEntrySelectionResolver` | horse IDをrace entry IDへ変換する。 |
| `SimulationBetPlanBuilder` | allocationから`SimulationBet`を構築しsnapshot化する。 |
| Repository | 完成したsnapshotとplan headerのallocation監査値を保存・復元する。 |
| `SimulationBetSource` | run・race・strategyに対応する保存済みbetsを供給する。 |

Allocatorはrecommendationの追加、削除、並べ替え、再評価、rank再採番、券種変更、selection変更、race entry解決、`SimulationBet`構築を行わない。budget不足時に下位候補を黙って削除せず、fail-closedで拒否する。候補数削減が必要なpolicyは、Allocatorではなく後続のbudget-aware selection責務として別設計する。

##### budget の正式入力契約

既存型にrace単位budgetはないため、後続契約で次を追加する。

```python
@dataclass(frozen=True, slots=True)
class BetStakeBudget:
    total_amount: int
```

`total_amount`は非負の非bool `int`かつ100円単位である。budgetはcomposition rootから明示的に渡す不変入力であり、現在時刻、Repository読取時刻、外部口座残高、Allocatorの隠れたmutable stateから取得しない。空planには0円または正の100円単位budgetを許可する。

recommendation件数を`N`とすると、購入候補がある場合の最低必要額は`N × 100円`である。`total_amount < N × 100円`なら、0円stake、100円未満stake、部分allocation、NO_BETへの変換を行わず、allocation不能としてfail-closedにする。

budgetはplan identityの構成要素にしない。同一identityは一つのimmutable snapshotだけを許すため、そのsnapshotに対応するallocationのbudgetは一意である。budgetは`BetAllocationPlan.total_budget`および後続schemaのplan header監査値として保存する。これにより、runをまたぐ同一strategyでも異なるbudgetを明示的に監査でき、actual stakeはsnapshot内の`SimulationBet.stake`から再現できる。

##### allocated recommendation と allocation plan

`BetRecommendation`と`BetPlan`はいずれもfrozen dataclassであり、recommendationsはtupleである。したがって、allocationはrecommendationをdeep copyせず、同じimmutable objectを参照してよい。

```python
@dataclass(frozen=True, slots=True)
class AllocatedBetRecommendation:
    recommendation: BetRecommendation
    purchase_order: int
    stake: int


@dataclass(frozen=True, slots=True)
class BetAllocationPlan:
    identity: SimulationBetPlanIdentity
    bet_plan: BetPlan
    allocations: tuple[AllocatedBetRecommendation, ...]
    total_budget: int

    @property
    def allocated_amount(self) -> int: ...

    @property
    def unallocated_amount(self) -> int: ...
```

`AllocatedBetRecommendation`は正式な`BetRecommendation`、0以上の非bool`purchase_order`、正の非bool100円単位`stake`を持つ。recommendationの内容・rankを変更しない。

`BetAllocationPlan`は`identity`、`bet_plan`、tuple化した`allocations`、非負100円単位の`total_budget`を保持する。`allocated_amount`と`unallocated_amount`はfieldではなくread-only propertyとし、前者を`sum(allocation.stake ...)`、後者を`total_budget - allocated_amount`から算出する。重複した集計fieldによる不整合を避けるためである。両値は100円単位で、`allocated_amount <= total_budget`を必須とする。

allocationは入力`BetPlan`を保持して1対1対応をdomain boundaryでも検証する。次を必須とする。

```text
len(allocations) == len(bet_plan.recommendations)
allocations[index].recommendation is bet_plan.recommendations[index]
allocations[index].purchase_order == index
```

`BetPlan`と`BetRecommendation`はfrozenであるため、object identityを使うことは可変オブジェクトへの依存ではなく、Allocatorが別のrecommendationを再構築・差し替えしていないことの明示的な保証になる。各allocationの順序・件数・recommendation内容は不変である。

plan内のrecommendation identityは`(bet_type, canonical horse_ids)`とする。`BetRecommendation`の`horse_ids`は`BetGenerator`で組合せを昇順化するが、allocation contractは入力`BetPlan`を再ソートしない。allocation planは重複identityを拒否し、後続Builderがrace entry IDsへ変換後に行う`SimulationBet`側の重複検証も維持する。

空`BetPlan`ではallocationも空とし、`allocated_amount == 0`、`unallocated_amount == total_budget`とする。これは正常なNO_BET候補であり、allocation失敗とは区別する。

##### `BetStakeAllocator` Protocol とpolicy再現性

```python
class BetStakeAllocator(Protocol):
    def allocate(
        self,
        *,
        identity: SimulationBetPlanIdentity,
        bet_plan: BetPlan,
        budget: BetStakeBudget,
    ) -> BetAllocationPlan:
        ...
```

同一入力・同一policy設定では決定的な結果を返す。DB、Repository、Provider、HTTP/network、logger、現在時刻、odds再取得、Result/Summary builder、Simulator、結果・払戻には依存しない。

allocation policyの名称、version、決定的設定はsimulation再現性に影響するため、具体Allocatorのクラス名だけで表現してはならない。現在の`strategy_config_hash()`は`StrategyConfig`の既存選択設定だけをhash化し、allocation policy・allocation設定を含まない。後続`Phase 4C-2d3b0a1`で、policy識別子・version・決定的設定を正式なstrategy configuration payloadへ追加し、`StrategyIdentity.strategy_config_hash`へ含める。**同じstrategy_config_hashで異なるallocation policyまたは設定を使用することは許可しない。**

budget値はpolicy設定ではなくrunごとの明示入力であるため、strategy config hashには含めない。budgetはallocation planと後続のplan header監査値へ保存する。

固定stake、均等配分、score比例、expected value比例、confidence比例、Kelly系、券種別上限は後続policyの比較対象である。Phase 4C-2d3b0aではいずれも採用しない。

##### Builder と次フェーズの進行判定

`SimulationBetPlanBuilder`は`BetAllocationPlan`からrecommendation、purchase order、stake、plan identityを取得する。stakeを再計算せず、allocationの一部を除外せず、recommendationを再ソートしない。

**Phase 4C-2d3b0a1へ進行可能**である。budget入力、budget不足、未使用budget、空plan、1対1対応、purchase order、allocation Protocol、policy hashの方向を確定した。0a1ではこれらのdomain / Protocol契約とstrategy configuration payloadへのpolicy設定取り込みを実装する。具体allocation algorithmは0a2まで実装しない。

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

`odds_snapshot_batches` と `payout_publications` は券種単位の親レコードであるため、単勝は完全・馬連は未取得のような状態を表現できる。`PayoutPublication` の `race_id + bet_type` 境界は、Provider接続executorが必要な払戻情報を解決する単位と一致する。`selection_key` は関連テーブルの昇順 `race_entry_id` 列から決定的に生成し、監査と一意制約に使う。参照整合性は関連テーブルで維持し、selection_keyだけに依存しない。

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
3. Rawデータ取得境界（`RaceSettlementSource`）と、既存変換Providerを使うProvider接続executorを追加する。
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
