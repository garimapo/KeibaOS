# KeibaOS Ver0.8 SimulationBet 複数券種化設計

## 1. Purpose

Ver0.8 の回収率シミュレーターで、1件の `SimulationBet` を「1レース・1券種・1つの正規化済み選択組合せ・1購入額」を表す不変の atomic bet として確定する。

対象券種は単勝、馬連、ワイド、3連複である。BOX、フォーメーション、購入候補の展開、レース単位の精算、ROI、最大ドローダウン、CLI はこの設計の対象外とする。

## 2. Current Contract

現行の `scripts/simulation/models.py` の `SimulationBet` は frozen dataclass であり、次のフィールドを持つ。

```python
SimulationBet(
    race_id: int,
    strategy_id: str,
    bet_type: str,
    race_entry_ids: Sequence[int],
    stake: int,
    recommendation_rank: int,
    placed_at_cutoff: datetime,
)
```

現状では `bet_type == "単勝"`、かつ `race_entry_ids` が1件でなければならない。`stake` は正の100円単位、選択IDは正の整数・重複なし・昇順タプルへ正規化される。`race_id` と `placed_at_cutoff` は必須である。

## 3. Current Usage Inventory

`SimulationBet` は simulation domain model、`SimulationResult`、既存モデルテスト、第4C-1aの `_evaluate_simulation_bet()` で利用されている。第4C-1aは `SimulationBet` が単勝専用であるため、単勝の atomic bet のみ評価している。

Repository境界の `scripts/simulation/repositories/interfaces.py` は、以下の4券種を `BET_TYPES` として定義し、`validate_bet_type()`、`normalize_selection()`、`selection_key()` を提供している。

| 券種 | 選択数 |
| --- | ---: |
| 単勝 | 1 |
| 馬連 | 2 |
| ワイド | 2 |
| 3連複 | 3 |

Odds/Payout Provider と Repository は、同じ `race_entry_ids` の正規化規則を既に使用している。

## 4. Problems With Win-Only Model

単勝固定のままでは、馬連・ワイド・3連複の払戻表を取得・保存できても、atomic bet として表せず、単一買い目精算へ接続できない。

また、評価ヘルパーのテストで複数券種を扱うために不正な `SimulationBet` を人工生成することは、公開コンストラクタの不変条件を破る。これは Fail Closed 方針と矛盾する。

## 5. Requirements

- 1つの `SimulationBet` は1券種、1 selection、1購入点を表す。
- 対象券種は単勝、馬連、ワイド、3連複だけとする。
- 馬番ではなく内部の `race_entry_id` を選択IDとして使用する。
- 選択は canonical な昇順 `tuple[int, ...]` とする。
- 券種別の選択数、重複、ID型、正数性は constructor で Fail Closed に検証する。
- `stake` は正の100円単位の `int` とする。
- `race_id`、strategy情報、順位、購入時点は現行どおり保持する。
- オッズ、払戻、結果、Provider、Repository、DB、CLI は保持・参照しない。

## 6. Supported Bet Types

対応する文字列は Repository 境界の `BET_TYPES` と完全に同じ値とする。

```text
単勝
馬連
ワイド
3連複
```

別名、空白の自動除去、英語名、未対応券種は許可しない。入力表記の解決は Provider/normalization の責務であり、`SimulationBet` は既に正規化された券種だけを受け取る。

## 7. Proposed SimulationBet Contract

後続の4C-1b1では、クラス名と constructor のフィールド順を変更せず、次の契約へ拡張する。

```python
@dataclass(frozen=True)
class SimulationBet:
    race_id: int
    strategy_id: str
    bet_type: str
    race_entry_ids: Sequence[int]
    stake: int
    recommendation_rank: int
    placed_at_cutoff: datetime
```

追加フィールド、factory method、別名 `AtomicSimulationBet`、`slots=True` は導入しない。既存の位置引数・キーワード引数・型名・frozen性との後方互換性を最優先する。

## 8. Invariants

`SimulationBet` constructor は次を保証する。

- `race_id` は bool ではない正の `int`。
- `strategy_id` は空でない文字列。
- `bet_type` は Repository境界の許可券種のいずれか。
- `race_entry_ids` は、券種に応じて1、2、2、3件の bool ではない正の `int`。
- selection 内の重複を拒否する。
- `stake` は bool ではない正の `int` かつ100円単位。
- `recommendation_rank` は bool ではない0以上の `int`。
- `placed_at_cutoff` は timezone-aware datetime。
- 生成後の `race_entry_ids` は tuple であり、フィールドは再代入できない。

constructor は list を許可するが、生成後に list 参照を保持しない。tuple以外の可変内部状態を保持しない。

## 9. Canonicalization

選択の正規化は Repository境界の `normalize_selection(race_entry_ids, bet_type)` と同じ規則を唯一の基準とする。

- `race_entry_ids` を昇順へ並べ替える。
- selection 内の順序は識別子に影響しない。
- 馬連 `(12, 11)` と `(11, 12)`、ワイド `(12, 11)` と `(11, 12)`、3連複の並べ替えは同じ selection になる。
- horse number は受け取らない。horse number からの解決は Provider の `resolve_selection()` で完了していなければならない。
- `selection_key` は保存・監査用の派生値であり、`SimulationBet` のフィールドには追加しない。

実装では `SimulationBet` が軽量な Repository境界の `validate_bet_type()` と `normalize_selection()` を再利用する。SQLite Repository、DB接続、Provider具象クラスは import しない。

## 10. Race Identity

`race_id` は現行どおり `SimulationBet` に保持する。

理由は、atomic bet がレース所属を明示し、`PayoutPublication.race_id` との照合を単一買い目評価時に Fail Closed で行えるためである。また、複数レースを扱う将来の入力で所属を失わない。

`race_id` の一致確認は constructor ではなく、bet と publication を結合する `_evaluate_simulation_bet()` の責務である。

## 11. Duplicate Bet Policy

1つの `SimulationBet` 内では duplicate selection を許可しない。

同一レース・同一strategyにおける同一 `(bet_type, race_entry_ids)` の複数購入点は、現行 `SimulationResult` が禁止している。この方針を維持する。従って stake や recommendation rank が異なっても、同じレース結果内で同じ selection を重ねて保持しない。

別strategy間の同一 selection は許可する。BOX/フォーメーションは上位の候補展開層が複数の atomic bet へ展開する責務であり、`SimulationBet` 自身は展開しない。

## 12. Backward Compatibility

次を維持する。

- 現行の単勝 constructor 呼び出しはすべて有効。
- フィールド名、順序、型名、frozen dataclass、等価比較、hash可能性を変えない。
- 単勝の `race_entry_ids=(id,)`、100円単位 stake、race_id・時点の検証結果を変えない。
- `SimulationResult` の購入額合計・重複 selection 検証は、新しい券種にも同じ意味で適用する。

変更は、単勝以外の許可券種と券種別 selection 数を受け入れることだけである。

## 13. Dependency Direction

許可する依存方向は次のとおりとする。

```text
simulation.models -> repositories.interfaces の純粋な券種・selection検証関数
providers -> simulation.models / repositories.interfaces
simulator -> simulation.models / repositories.interfaces
repositories.sqlite -> repositories.interfaces
```

禁止する依存は、`simulation.models` から SQLite Repository、Provider具象クラス、migration、HTTP、CLI、main、DB接続への依存である。循環 import を作らない。

将来、共有規則を独立した値オブジェクトモジュールへ移す必要が生じた場合は、その移行を別設計・別変更として扱う。本段階では券種規則を二重実装しない。

## 14. Single-Bet Evaluation Impact

`_evaluate_simulation_bet()` は、次の照合規則を維持する。

```text
(bet.bet_type, bet.race_entry_ids)
==
(publication.bet_type, payout_record.race_entry_ids)
```

`race_id` も一致しなければ `SimulationBetEvaluationError` とする。各券種の selection 数を評価ヘルパーで独自に再検証しない。`SimulationBet` と `PayoutPublication` の公開境界モデルが不変条件を保証するためである。

WINNING、REFUND、VOID、UNSUPPORTEDの精算方針、未完全 publication の Fail Closed、端数を許容しない払戻算出は第4C-1aのまま維持する。

## 15. Single-Race Evaluation Impact

レース単位の精算は後続段階で、同一 `race_id` の複数 atomic bet を順に評価して集約する。その段階でも各 bet はこの設計の `bet_type` と canonical `race_entry_ids` により一意に結合される。

本設計は `SimulationResult`、購入金額配分、券種間の優先順位、BOX/フォーメーション展開、ROI集計を変更しない。

## 16. Migration Plan

4C-1b1では、次を実施する。

1. `SimulationBet` の単勝固定検証を Repository境界の券種検証へ置換する。
2. selection を `normalize_selection()` で canonical tuple にする。
3. 単勝・馬連・ワイド・3連複、正規化、券種別選択数、互換性の単体テストを追加する。
4. 既存の simulation model テストと第4C-1aテストを更新して回帰を確認する。

4C-1b2では、単一買い目評価ヘルパーを4券種の atomic bet で確認する。4C-1c以降でレース単位評価、精算モデル、ROI/資金曲線を扱う。

## 17. Test Plan

最小限、以下を個別に検証する。

- 単勝、馬連、ワイド、3連複の正常生成。
- 各券種の選択数不足・過多の拒否。
- 未対応券種、空文字、bool ID、0/負数ID、重複IDの拒否。
- 順序の異なる selection が同じ canonical tuple になること。
- list 入力後の変更が生成済み bet に影響しないこと。
- stake の0、負数、bool、100円単位でない値の拒否。
- race_id、時点、strategy_id、rank の既存不変条件。
- 等価比較とhashが canonical selection に従うこと。
- 既存の単勝 constructor が互換であること。
- Provider、SQLite、DB、network、CLIを import しないこと。
- 第4C-1a評価で、4券種の matching `PayoutPublication` と一致すること。

## 18. Risks

- `SimulationResult` の重複検出は selection と券種を基準にしているため、同一selectionの複数回購入を必要とする将来要件とは両立しない。これは本設計では意図的に禁止する。
- `simulation.models` から Repository境界の純粋関数を利用するため、interfaces.pyの軽量性を維持する必要がある。
- 日本語券種文字列は保存済みスキーマとRepository境界に合わせる必要があり、別表記を自動補正してはならない。
- 払戻表の完全性・返還・不成立の意味判断は Provider/Repository境界が担い、`SimulationBet` に持ち込まない。

## 19. Rejected Alternatives

### `AtomicSimulationBet` を新設する

却下する。既存呼び出し、テスト、シリアライズ、型参照を二重化し、単勝専用であるという制約だけを解くための変更としては広すぎる。

### 券種ごとの subclass を作る

却下する。券種別選択数以外のフィールド・挙動は同じであり、代数的な識別子と重複する。

### Factory method のみで複数券種を作る

却下する。public constructor が不正値を受け入れるままになり、既存の直接 constructor 使用との検証差が生じる。

### `race_id` を削除する

却下する。publicationとの所属照合、将来の複数レース処理、atomic betの監査可能性を失う。

### `selection_key` をフィールドに保存する

却下する。`selection_key` は `bet_type` と canonical selection から決定できる派生値であり、二重保持は不整合の原因になる。

### BOX/フォーメーションを `SimulationBet` に持たせる

却下する。atomic selection の一意性、払戻レコード照合、stakeの意味を壊す。展開は上位層の責務である。

## 20. Final Decision

`SimulationBet` を既存の名前・constructor signature・frozen dataclassのまま、4券種を表現できる atomic bet に拡張する。

券種の許可値と selection 数は Repository境界の `validate_bet_type()` と `normalize_selection()` を唯一の規則として再利用する。`race_id` は維持し、selection は `race_entry_id` の canonical tuple とする。重複 selection、BOX、フォーメーション、オッズ・払戻・結果・永続化情報は保持しない。

## 21. Implementation Phases

1. **4C-1b0（本書）**: 契約・依存方向・互換性を確定する。コードを変更しない。
2. **4C-1b1**: `SimulationBet` の4券種化とモデルテストを実装する。
3. **4C-1b2**: `_evaluate_simulation_bet()` を4券種 atomic bet に接続し、払戻照合テストを拡張する。
4. **4C-1c**: レース単位で複数 atomic bet を評価する純粋ロジックを実装する。
5. **4C-2以降**: 精算、集計、ROI、最大ドローダウン、CLIを段階的に追加する。

各段階は、DB、Provider、Repository、CLIを必要以上に変更せず、独立したテストとレビューを経て進める。
