# Ver0.8 非精算系 `SimulationResult` 設計

## 1. Purpose

本書は、1レース・1 Strategy の `SimulationResult` における非精算状態を定義する。対象は `UNSETTLED`、`VOID`、`ERROR`、`UNSUPPORTED` であり、既存の `SETTLED` と `NO_BET` を変更しない。目的は、払戻未確定・公式なレース無効・未対応データ・実行異常を混同せず、ROIへ未精算金額を混入させないことにある。

今回の成果物は設計書のみである。production code、test code、DB、Provider、Repository、CLI、集計実装を変更しない。

## 2. Existing `SimulationResult` Contract

現行モデルは frozen dataclass であり、constructorのフィールド順は次のとおりである。

1. `race_id`
2. `strategy_id`
3. `bets`
4. `settlement_status`
5. `exclusion_reason`
6. `planned_investment`
7. `settled_investment`
8. `payout`
9. `profit`
10. `hit_bet_count`
11. `settled_at`

全状態で `planned_investment == sum(bet.stake for bet in bets)`、betの race/strategy 所属、重複identity（`bet_type + race_entry_ids`）禁止を満たす。非 `SETTLED` では `settled_investment`、`payout`、`profit`、`settled_at` はすべて `None`、`hit_bet_count` は0でなければならない。

## 3. Status Definitions

| 状態 | 意味 | 精算可能性 |
| --- | --- | --- |
| `UNSETTLED` | 有効なbetsはあるが、必要な公式精算データが未確定・未取得・不完全である | 将来再試行可能 |
| `VOID` | レース全体が公式に無効・取消・不成立等で、通常精算すべきではない | 原則として通常精算しない |
| `ERROR` | 内部整合性、入力契約、Provider出力、予期しない実行異常をFail Closedで検出した | 原因修正後のみ再実行 |
| `UNSUPPORTED` | データは存在するが、現行KeibaOSが安全に扱えない公式状態・券種・精算規則である | 機能追加まで精算しない |

`SETTLED` は実払戻により確定した状態、`NO_BET` は候補が生成されず購入予定額0の状態であり、本書の非精算系には含めない。

## 4. Status Priority

複数の事実が同時にある場合は、次の優先順位で1つだけを選ぶ。

1. `ERROR`
2. `VOID`
3. `UNSUPPORTED`
4. `UNSETTLED`
5. `SETTLED`
6. `NO_BET`

例として、Providerが `UNSUPPORTED` を返していても内部検証で不正な出力を検出した場合は `ERROR` とする。公式レース無効と払戻未取得が併存する場合は `VOID` とする。優先順位は将来のstatus decision helperが一元管理し、各呼出し元が個別に解釈してはならない。

## 5. Bet Preservation Policy

`UNSETTLED`、`VOID`、`UNSUPPORTED` は、候補生成済みの `SimulationBet` を保持する。`ERROR` は異常発生時点により空betsまたは生成済みbetsを許可する。betsが存在する場合、すべて現行モデル契約に従い、planned investmentはstake合計となる。

空betsを許可するのは、Strategy実行前、bet生成前、または入力検証段階で発生した `ERROR` に限る。`UNSETTLED`、`VOID`、`UNSUPPORTED` に空betsを許可するかは、当該状態がbet生成後のみであるという将来のbuilder契約で明示的に禁止する。

## 6. Monetary Contract

非精算系4状態では次を共通契約とする。

- `settled_investment is None`
- `payout is None`
- `profit is None`
- `settled_at is None`
- `hit_bet_count == 0`

`planned_investment` はbetsのstake合計だけを表す。これは購入予定・候補生成済みという監査値であり、ROIに投入済み金額として扱ってはならない。`payout=0`、`profit=-planned_investment`、`settled_investment=0` への置換は、未精算と不的中を混同するため禁止する。VOIDに対して返還額を推測することも禁止する。

## 7. Exclusion Reason Contract

`UNSETTLED`、`VOID`、`ERROR`、`UNSUPPORTED` は非空の `exclusion_reason` を必須とする。`SETTLED` と `NO_BET` は必ず `None` とする。

reasonは表示文ではなく、安定した小文字snake_caseのreason codeとする。日時、例外repr、機密値、自由文、prefix付きの臨時形式は保存しない。初期候補は次のとおりである。

- `missing_payout_publication`
- `incomplete_payout_publication`
- `race_void`
- `unsupported_payout_status`
- `unsupported_race_result_status`
- `internal_evaluation_error`
- `invalid_provider_output`

Provider側reasonをそのまま転記せず、race orchestration境界で本契約のreasonへ正規化する。

## 8. Provider Completeness Mapping

Providerの `CompletenessStatus` はそのまま `SettlementStatus` ではない。初期の対応は次のとおりとする。

| CompletenessStatus | 基本の結果状態 | 備考 |
| --- | --- | --- |
| `COMPLETE` | 次の事実判定へ進む | 単独ではSETTLEDを保証しない |
| `INCOMPLETE` | `UNSETTLED` | 公式データ待ち・不完全表 |
| `UNSUPPORTED` | `UNSUPPORTED` | 明示的な未対応 |
| `INVALID` | `ERROR` | Provider契約または整合性違反 |

ただし、公式レースVOIDが確認できる場合は `VOID` を優先する。欠落publicationのように正常な不在を表す事実は `ERROR` ではなく `UNSETTLED` とする。Provider例外をすべてERRORにする実装は禁止し、利用可能な事実と例外種別により区別する。

## 9. Race Result Mapping

`RaceResultStatus.COMPLETE` は結果が通常精算に利用可能であることを示す。`PARTIAL` は基本的に `UNSETTLED`、`VOID` は `VOID`、`UNSUPPORTED` は `UNSUPPORTED` へ写像する。

レース結果がVOIDである場合は、Payout publicationが欠落または不完全でも `VOID` を優先する。公式結果が不正、またはstatusとentriesが矛盾しProviderがINVALIDを返す場合は `ERROR` とする。現在時刻や後日取得情報で結果を補うことはしない。

## 10. Payout Status Mapping

`PayoutStatus` は個別recordの状態であり、race-level `SettlementStatus` と同一視しない。

- `WINNING` と `REFUND` は、完全表・他の必要事実が揃う場合に通常精算の材料となる。
- `VOID` recordだけではレース全体を `VOID` にしない。公式レース無効というrace-level事実が必要である。
- `UNSUPPORTED` recordが1件でも必要な精算対象に含まれる場合は、部分精算せずrace全体を `UNSUPPORTED` とする。

組合せ券種の不的中は、完全な払戻表に対象selectionが存在しないことで表す。0円のwinning行を合成しない。

## 11. Exception Classification

次の異常は、利用可能な正常事実がない限り `ERROR` とする。

- `SimulationBetEvaluationError`
- `ProviderValidationError`
- `RepositoryValidationError`
- `RepositoryDataIntegrityError`
- `RepositoryConflictError`
- `TypeError`、`ValueError`、`KeyError`、`ArithmeticError`

ただし、missing publicationやincomplete publicationのように設計上想定された未確定事実を例外化している場合は、呼出し境界で `UNSETTLED` に分類する。例外名のみで分類せず、すでに取得済みのcomplete/void/unsupported事実と失敗地点を併用する。

## 12. Result Construction Boundary

単一bet評価と複数bet評価は、成功時のみ内部評価値を返す。非精算系 `SimulationResult` は、次のrace orchestration境界でのみ生成する。

- Provider結果・公式status・publication完全性を集約した後
- 非精算の理由を1つに確定した後
- betsとplanned investmentを監査可能な形で確定した後

単一bet helper、`_evaluate_simulation_race_bets`、Provider、Repositoryは非精算 `SimulationResult` を直接生成しない。これにより、status決定・reason正規化・優先順位が分散しない。

## 13. Builder API Decision

次フェーズでは共通の非公開builderを導入する。

```python
_build_non_settled_simulation_result(
    *,
    race_id: int,
    strategy_id: str,
    bets: Sequence[SimulationBet],
    settlement_status: SettlementStatus,
    exclusion_reason: str,
) -> SimulationResult
```

このbuilderは `UNSETTLED`、`VOID`、`ERROR`、`UNSUPPORTED` だけを許可し、`SETTLED` と `NO_BET` を拒否する。入力をtuple化し、planned investmentをbetsのstake合計として渡し、精算金額・時刻をすべて `None`、的中数を0としてkeyword-onlyで構築する。

初期実装ではstatus別wrapperを作らない。共通builderを先に実装してから、API重複または呼出し側の誤指定が実測で問題になった場合にのみ薄いwrapperを検討する。

## 14. Aggregation and ROI Denominators

`SimulationSummary.race_count` は全statusを数える。各statusの件数は排他的で、その合計はrace_countに一致する。

- `settled_race_count`: `SETTLED` のみ
- `unsettled_race_count`: `UNSETTLED` のみ
- `no_bet_race_count`: `NO_BET` のみ
- `void_race_count`: `VOID` のみ
- `error_race_count`: `ERROR` のみ
- `unsupported_race_count`: `UNSUPPORTED` のみ
- `bet_count`: 全statusのbets数
- `settled_bet_count`: `SETTLED` のbets数のみ

investment、payout、profit、ROI、的中率、最大ドローダウンは `SETTLED` のみで算出する。非精算のplanned investmentはROI分子・分母、hit rate、drawdownに含めない。分母0の率は `None` とし、表示は `N/A` とする。

## 15. Settled Time Policy

非精算系の `settled_at` は常に `None` とする。VOIDの公式確定時刻やProviderのobserved_atを `settled_at` に流用しない。資金曲線の時系列は、精算金額を持つ `SETTLED` のみを、その確定済み精算時刻で並べる。

将来、VOID確定時刻を監査用途に保存する必要が生じても、`SimulationResult.settled_at` の意味を拡張せず、別の監査フィールドまたはresult source recordで扱う。

## 16. Error Before and After Bet Creation

ERRORのbetsはエラー地点に依存する。

| エラー地点 | bets | planned_investment |
| --- | --- | --- |
| Strategy実行前、入力時点検証、bet生成前 | 空tuple | 0 |
| bet生成後、publication収集後、評価中、結果構築中 | 生成済みbets | stake合計 |

ERRORでbetsを捏造せず、生成済みbetsを空へ置き換えず、planned investmentを実際のbetsと矛盾させない。これにより診断と将来の再実行判断に必要な監査情報を保つ。

## 17. Fail Closed Rules

- 非精算状態に0円の精算金額を代入しない。
- reason欠損、空文字、非文字列、許可外statusは拒否する。
- status決定不能時は推測でSETTLED、VOID、UNSETTLEDを選ばず `ERROR` とする。
- 1券種でも必要なpublicationが不完全なら部分ROIを作らず、race全体を非精算とする。
- unsupported recordを無視して残りbetsだけを精算しない。
- race/strategy/bet所属・duplicate identity・planned investmentのモデル不変条件を回避しない。
- 現在時刻、DBの最新状態、後日取得データを使って過去の非精算状態を補完しない。

## 18. Rejected Alternatives

次の案は採用しない。

- `UNSETTLED` を不的中（payout=0）として保存する案
- VOIDを返還額や投資額と同額のpayoutへ推測変換する案
- `PayoutRecord.VOID` だけでrace-level VOIDにする案
- Provider例外を無条件にERRORへ写像する案
- statusごとの独立builderを先に4本作る案
- 非精算状態にsettled_atを記録する案
- 生成済みbetsをERRORで常に破棄する案
- status優先順位を各Providerや各helperへ分散する案

## 19. Final Decision

非精算4状態は排他的な `SimulationResult` 状態として維持する。実装は共通の `_build_non_settled_simulation_result` を起点にし、status decisionはその前段のrace orchestrationで一元化する。金額・払戻・収支・精算時刻・的中数はSETTLED以外で確定値に見せない。

ERROR、VOID、UNSUPPORTED、UNSETTLEDの優先順位は本書の順序に固定し、個別record statusやProvider completenessを直接race statusと同一視しない。

## 20. Implementation Phases

1. **4C-1c2c1**: 共通非精算builder、入力検証、`SimulationResult` 変換テストを実装する。
2. **4C-1c2c2**: Provider completeness、race result、publication事実、例外分類からstatusを決定する純粋helperを実装する。
3. **4C-1c3**: 単一race orchestrationで成功評価・NO_BET・非精算決定を統合する。
4. **後続**: 複数race集計、ROI、drawdown、report/CLIへ接続する。

各フェーズは前段の契約を変えず、対象ファイル・テスト・commitを分割してレビューする。

## 21. Test Plan

次フェーズの最小テストは次を含む。

- 4非精算statusそれぞれでbets、planned investment、reason、全精算フィールドNone、hit数0を検証する。
- `SETTLED` と `NO_BET` を共通非精算builderが拒否する。
- race_id、strategy_id、bets、reason、statusの不正入力をFail Closedで拒否する。
- ERRORの空betsと生成済みbetsの両方を検証する。
- reason不足、精算金額混入、settled_at混入、hit数非0をモデル契約で拒否する。
- status priorityの競合事実を検証する。
- provider completeness、race result status、payout statusの対応表をテストする。
- ROI・drawdown・DB・Provider I/Oをbuilderが実行しないことを確認する。

同着、返還、取消、不成立の詳細精算規則は、公式仕様が確定するまで推測実装しない。

## 22. Risks

- 公式sourceごとのVOID・返還・不成立表現が未確定である。
- Providerが「欠落」と「異常」を十分に区別できない場合、UNSETTLEDとERRORの分類根拠が不足する。
- 複数券種の一部だけが未対応・不完全な場合は、初期方針どおりrace全体を非精算とするため、利用可能な部分データをROIへ使えない。
- `SimulationSummary` のbet_countは全bets、金額・率はSETTLEDのみという二重の母集団を、CLI/reportで明示しなければ誤読を招く。
- status優先順位を変更する場合は、既存reportと正式ROIの比較可能性へ影響するため、設計書・テスト・マイグレーション記録を同時に更新する必要がある。
