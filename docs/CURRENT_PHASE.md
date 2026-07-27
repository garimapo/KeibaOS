Commit 86b87dbで引継ぎワークフローは稼働開始です。今後は長大な指示をCodexへ貼らず、CURRENT_PHASE.mdだけ差し替えます。ようやくコピペ係から少し昇進です。

docs/CURRENT_PHASE.mdの内容を、以下へ置き換えてください。
Current Phase
Status

READY_FOR_CODEX
Phase

Phase 4C-2d3b1e1
RaceEntrySource Protocol contract
Base Commit

86b87db
Branch

feature/ver0.8-simulator
Objective

Prediction側のhorse ID selectionを、race-scoped entry IDへ解決するための読取境界として、RaceEntrySource Protocolと専用契約テストを追加する。

今回はProtocol contractだけを実装する。

SQLite具象Source、Repository-backed Resolver、Builder接続、Snapshot Repository変更、Pipeline接続には進まない。
Allowed Files

変更可能なファイルは次だけとする。

scripts/simulation/race_entry_source.py
tests/test_race_entry_source_contract.py
docs/LATEST_CODEX_REPORT.md

Forbidden Files

次を変更しない。

database/keiba.db
logs/
logs/配下すべて
docs/CURRENT_PHASE.md
docs/VER0.8_SIMULATOR_DESIGN.md
AGENTS.md
scripts/simulation/selection_resolver.py
scripts/simulation/bet_plan_builder.py
scripts/simulation/bet_plan_snapshot.py
scripts/simulation/repositories/
scripts/migrations/
その他のproductionコード
その他のtests
schema
migration
CLI
settings

Required Contracts

正式なProtocol名:

RaceEntrySource

正式API:

from typing import Mapping, Protocol, Sequence


class RaceEntrySource(Protocol):
    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        ...

契約上の意味:

戻り値key   = requested prediction horse ID
戻り値value = 指定race内の正式race entry ID

BetRecommendation.horse_idsは現行モデルではhorses.id由来だが、Source境界ではrace所属と対応関係を明示的に解決する。

物理的に同じ整数値であっても、horse IDとrace entry IDを無検証で同一視しない。
Implementation Requirements

    typing.Protocolを使用する

    runtime_checkableを使用しない

    public methodはload_race_entry_id_mapだけ

    method本文は...だけ

    全引数をkeyword-onlyにする

    race_id annotationはint

    horse_ids annotationはSequence[int]

    戻り値annotationはMapping[int, int]

    default引数を追加しない

    *argsを追加しない

    **kwargsを追加しない

    asyncにしない

    concrete behaviorを追加しない

    validation処理を追加しない

    SQLを追加しない

    SQLiteをimportしない

    Repository例外をimportしない

    Stubやin-memory実装をproductionへ追加しない

    package root exportは既存の明示export規約がある場合だけ検討する

    exportによって循環importが起きる場合は直接module importとする

    新しい例外classを追加しない

Protocolが将来の具象Sourceへ要求する意味:

    1 selectionをbatchで解決する

    horse単位のN+1 queryを行わない

    SQL row順へ依存しない

    requested horse IDとの対応をmappingで返す

    missing IDを暗黙補完しない

    wrong-race IDを別raceから取得しない

    requested以外の余分なmappingを返さない

    duplicate resolutionを黙認しない

ただし、これらのruntime validationやDB処理は今回実装しない。
Validation and Error Handling

今回のProtocol moduleにはvalidation・例外処理を実装しない。

将来の正式分担:

Resolver:
- public API入力validation
- empty selection
- duplicate horse IDs
- Source戻り値contract
- missing／wrong-raceのValueError化
- 入力順でのtuple再構成

SQLite RaceEntrySource:
- connection利用条件
- batch query
- DB row型
- DB重複
- race所属
- RepositoryValidationError
- RepositoryDataIntegrityError

今回、新例外を定義・再定義しない。
Required Tests

専用テストで最低限、次を確認する。
Protocol構造

    RaceEntrySourceがProtocolである

    runtime-checkableではない

    public methodはload_race_entry_id_mapだけ

    method本文が宣言のみ

    concrete instance storageを持たない

    SQLやSQLite実装を持たない

Signature

    race_idがkeyword-only

    horse_idsがkeyword-only

    引数順が正式順

    defaultなし
    -可変長引数なし

    asyncではない

    race_id: int

    horse_ids: Sequence[int]

    -> Mapping[int, int]

inspect.signature()およびtyping.get_type_hints()を既存テスト規約に従って使用する。
構造的適合

tests内だけに次の最小Stubを作成してよい。

class StubRaceEntrySource:
    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        return {horse_id: horse_id for horse_id in horse_ids}

このStubはsignature確認専用であり、productionのidentity変換実装ではない。

確認:

    構造的にmethodを実装可能

    runtime isinstance判定は行わない

    productionへStubを追加しない

依存境界

Production moduleが次へ依存しないことを確認する。

sqlite3
database module
Repository具象実装
Repository例外
RaceEntrySelectionResolver具象実装
SimulationBetPlanBuilder
Snapshot Repository
Provider
PredictionPipeline
Simulator
Result
Summary
CLI
settings
HTTP
network
current time

回帰確認

最低限、以下を実行する。

tests/test_race_entry_source_contract.py
tests/test_race_entry_selection_resolver_contract.py
tests/test_simulation_bet_plan_builder.py
tests/test_simulation_bet_plan_snapshot.py
tests/test_simulation_bet_plan_snapshot_repository_contract.py
tests/test_sqlite_simulation_bet_plan_snapshot_repository.py

関連テスト後、全pytestを実行する。
Search Checks

最低限、次を確認する。

git grep -n "class RaceEntrySource" -- scripts tests
git grep -n "load_race_entry_id_map" -- scripts tests
git grep -n "target_race_count" -- scripts tests

新規未追跡ファイルがgit grepに出ない場合は、rg等でworktreeも確認する。

期待結果:

    productionのRaceEntrySource定義は新規moduleだけ

    production具象Sourceは0件

    SQLite queryは0件

    Repository-backed Resolverは未実装

    productionへtarget_race_count追加なし

Git Safety

stage、commit、pushは禁止。

常に禁止:

git add .
git add -A
git commit -a
git clean
git reset
git restore
git stash
git commit --amend
git rebase
force push

次を操作・stage・commitしない。

database/keiba.db
logs/
logs/配下すべて

作業終了時に必ず実行する。

git diff --check
git status --short

Completion Report

作業完了後、docs/LATEST_CODEX_REPORT.mdを今回の結果で置き換える。

最低限、次を報告する。

    変更ファイル一覧

    Protocol配置

    最終class定義

    method最終signature

    keyword-only契約

    annotations

    戻り値annotation

    runtime_checkable使用有無

    public method一覧

    method本文

    Source mappingの意味

    import依存方向

    package export変更有無

    新例外追加有無

    追加したテスト内容

    専用テスト結果

    Resolver／Builder／Snapshot関連テスト結果

    Repository関連テスト結果

    全pytest結果

    git diff --check結果

    検索結果

    git status --short

    想定commit対象

    SQLite Source未実装

    Repository-backed Resolver未実装

    PersistedSimulationBetSource未実装

    Pipeline未接続

    database/keiba.dbとlogs/を操作していないこと

    stage・commit・push未実施

    blockerの有無

Stop Condition

以下の場合は作業を停止し、LATEST_CODEX_REPORT.mdへ報告する。

    設計書と実在contractが衝突する

    Allowed Files外の変更が必要

    Protocolだけでは成立せずschema変更が必要

    package exportに循環importが発生する

    テスト失敗の原因が今回の範囲外

    Git statusに想定外ファイルがある

    不明な既存挙動を推測する必要がある

実装・テスト・報告後は、stage・commit・pushせずレビュー待ちで停止する。

保存したら、Codexにはこれだけ送ります。

AGENTS.mdとdocs/CURRENT_PHASE.mdを読み、記載されたフェーズを実施してください。

完了後はdocs/LATEST_CODEX_REPORT.mdを更新し、stage・commit・pushせずレビュー待ちで停止してください。

Codex完了後は、docs/LATEST_CODEX_REPORT.mdをこのチャットへ添付すればレビューできます。今回はCURRENT_PHASE.mdの内容を一度貼る必要がありますが、以後のCodex側への指示は下の短文だけです。

停止しました。実装は開始していません。

添付指示は READY_FOR_CODEX / Phase 4C-2d3b1e1 を示していますが、実際の [CURRENT_PHASE.md](C:\Users\garim\Desktop\KeibaAI\docs\CURRENT_PHASE.md) は次のままです。

text
Status: WAITING_FOR_PHASE_INSTRUCTION
Allowed Files: None



AGENTS.mdはこのファイルに記載された範囲だけを実施するよう定めており、添付指示側でもdocs/CURRENT_PHASE.mdは変更禁止です。そのため、許可された実装範囲を確定できません。

docs/CURRENT_PHASE.mdをPhase 4C-2d3b1e1の内容へ更新・承認した後に、改めて指示してください。database/keiba.db、logs/、コード、テスト、Git状態には変更を加えていません。

Codexの判断が正しいです。こちらの手順抜けでした。

このファイルをダウンロードして、

C:\Users\garim\Desktop\KeibaAI\docs\CURRENT_PHASE.md

へ上書きしてください。

上書き後、Codexにはこれだけ送れば進みます。

AGENTS.mdとdocs/CURRENT_PHASE.mdを読み、記載されたフェーズを実施してください。

完了後はdocs/LATEST_CODEX_REPORT.mdを更新し、stage・commit・pushせずレビュー待ちで停止してください。

今後は毎回、私がCURRENT_PHASE.mdそのものをダウンロードできる形で出します。これなら長文コピペは不要です。

Phase 4C-2d3b1e1 を実装し、レビュー待ちで停止しました。

- 追加: [race_entry_source.py](C:\Users\garim\Desktop\KeibaAI\scripts\simulation\race_entry_source.py)
- 追加: [test_race_entry_source_contract.py](C:\Users\garim\Desktop\KeibaAI\tests\test_race_entry_source_contract.py)
- 更新: [LATEST_CODEX_REPORT.md](C:\Users\garim\Desktop\KeibaAI\docs\LATEST_CODEX_REPORT.md)

RaceEntrySource は keyword-only の load_race_entry_id_map() だけを持つ非runtime-checkable Protocolです。SQL・SQLite・Repository・具象Source・Resolver接続は追加していません。

テスト結果:

- 専用: 16 passed
- 関連回帰: 159 passed
- 全pytest: 2150 passed, 2 skipped

git diff --check は、変更禁止のユーザー更新ファイル [CURRENT_PHASE.md](C:\Users\garim\Desktop\KeibaAI\docs\CURRENT_PHASE.md) 114行目の既存末尾空白だけを検出しています。Codex変更ファイルのdiffエラーはありません。

最終status:

text
 M database/keiba.db
 M docs/CURRENT_PHASE.md
 M docs/LATEST_CODEX_REPORT.md
?? logs/
?? scripts/simulation/race_entry_source.py
?? tests/test_race_entry_source_contract.py



stage・commit・pushは未実施です。

実装報告自体は問題なさそうです。ただし、commit承認はまだ保留にします。こちらからはC:\...のローカルファイル本文を読めないため、実コードを見ずに承認するのは雑すぎます。

まず、修正版でこちらを上書きしてください。

配置先:

C:\Users\garim\Desktop\KeibaAI\docs\CURRENT_PHASE.md

その後、Codexへこれだけ送ります。

docs/CURRENT_PHASE.mdの末尾空白だけを修正しました。productionコードとテストは変更していません。

以下を再実行してください。

git diff --check
git status --short

結果をdocs/LATEST_CODEX_REPORT.mdへ反映し、stage・commit・pushせず停止してください。コード変更がないためpytestの再実行は不要です。

完了後、このチャットへ次の4ファイルを実ファイルとして添付してください。

scripts/simulation/race_entry_source.py
tests/test_race_entry_source_contract.py
docs/LATEST_CODEX_REPORT.md
docs/CURRENT_PHASE.md

それを確認してから、Phase 4C-2d3b1e1の正式レビューとcommit承認を出します。


CURRENT_PHASE_clean.md
Current Phase
Status

READY_FOR_CODEX
Phase

Phase 4C-2d3b1e1
RaceEntrySource Protocol contract
Base Commit

86b87db
Branch

feature/ver0.8-simulator
Objective

Prediction側のhorse ID selectionを、race-scoped entry IDへ解決するための読取境界として、RaceEntrySource Protocolと専用契約テストを追加する。

今回はProtocol contractだけを実装する。

SQLite具象Source、Repository-backed Resolver、Builder接続、Snapshot Repository変更、Pipeline接続には進まない。
Allowed Files

変更可能なファイルは次だけとする。

scripts/simulation/race_entry_source.py
tests/test_race_entry_source_contract.py
docs/LATEST_CODEX_REPORT.md

Forbidden Files

次を変更しない。

database/keiba.db
logs/
logs/配下すべて
docs/CURRENT_PHASE.md
docs/VER0.8_SIMULATOR_DESIGN.md
AGENTS.md
scripts/simulation/selection_resolver.py
scripts/simulation/bet_plan_builder.py
scripts/simulation/bet_plan_snapshot.py
scripts/simulation/repositories/
scripts/migrations/
その他のproductionコード
その他のtests
schema
migration
CLI
settings

Required Contracts

正式なProtocol名:

RaceEntrySource

正式API:

from typing import Mapping, Protocol, Sequence


class RaceEntrySource(Protocol):
    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        ...

契約上の意味:

戻り値key   = requested prediction horse ID
戻り値value = 指定race内の正式race entry ID

BetRecommendation.horse_idsは現行モデルではhorses.id由来だが、Source境界ではrace所属と対応関係を明示的に解決する。

物理的に同じ整数値であっても、horse IDとrace entry IDを無検証で同一視しない。
Implementation Requirements

    typing.Protocolを使用する

    runtime_checkableを使用しない

    public methodはload_race_entry_id_mapだけ

    method本文は...だけ

    全引数をkeyword-onlyにする

    race_id annotationはint

    horse_ids annotationはSequence[int]

    戻り値annotationはMapping[int, int]

    default引数を追加しない

    *argsを追加しない

    **kwargsを追加しない

    asyncにしない

    concrete behaviorを追加しない

    validation処理を追加しない

    SQLを追加しない

    SQLiteをimportしない

    Repository例外をimportしない

    Stubやin-memory実装をproductionへ追加しない

    package root exportは既存の明示export規約がある場合だけ検討する

    exportによって循環importが起きる場合は直接module importとする

    新しい例外classを追加しない

Protocolが将来の具象Sourceへ要求する意味:

    1 selectionをbatchで解決する

    horse単位のN+1 queryを行わない

    SQL row順へ依存しない

    requested horse IDとの対応をmappingで返す

    missing IDを暗黙補完しない

    wrong-race IDを別raceから取得しない

    requested以外の余分なmappingを返さない

    duplicate resolutionを黙認しない

ただし、これらのruntime validationやDB処理は今回実装しない。
Validation and Error Handling

今回のProtocol moduleにはvalidation・例外処理を実装しない。

将来の正式分担:

Resolver:
- public API入力validation
- empty selection
- duplicate horse IDs
- Source戻り値contract
- missing／wrong-raceのValueError化
- 入力順でのtuple再構成

SQLite RaceEntrySource:
- connection利用条件
- batch query
- DB row型
- DB重複
- race所属
- RepositoryValidationError
- RepositoryDataIntegrityError

今回、新例外を定義・再定義しない。
Required Tests

専用テストで最低限、次を確認する。
Protocol構造

    RaceEntrySourceがProtocolである

    runtime-checkableではない

    public methodはload_race_entry_id_mapだけ

    method本文が宣言のみ

    concrete instance storageを持たない

    SQLやSQLite実装を持たない

Signature

    race_idがkeyword-only

    horse_idsがkeyword-only

    引数順が正式順

    defaultなし

    可変長引数なし

    asyncではない

    race_id: int

    horse_ids: Sequence[int]

    -> Mapping[int, int]

inspect.signature()およびtyping.get_type_hints()を既存テスト規約に従って使用する。
構造的適合

tests内だけに次の最小Stubを作成してよい。

class StubRaceEntrySource:
    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        return {horse_id: horse_id for horse_id in horse_ids}

このStubはsignature確認専用であり、productionのidentity変換実装ではない。

確認:

    構造的にmethodを実装可能

    runtime isinstance判定は行わない

    productionへStubを追加しない

依存境界

Production moduleが次へ依存しないことを確認する。

sqlite3
database module
Repository具象実装
Repository例外
RaceEntrySelectionResolver具象実装
SimulationBetPlanBuilder
Snapshot Repository
Provider
PredictionPipeline
Simulator
Result
Summary
CLI
settings
HTTP
network
current time

回帰確認

最低限、以下を実行する。

tests/test_race_entry_source_contract.py
tests/test_race_entry_selection_resolver_contract.py
tests/test_simulation_bet_plan_builder.py
tests/test_simulation_bet_plan_snapshot.py
tests/test_simulation_bet_plan_snapshot_repository_contract.py
tests/test_sqlite_simulation_bet_plan_snapshot_repository.py

関連テスト後、全pytestを実行する。
Search Checks

最低限、次を確認する。

git grep -n "class RaceEntrySource" -- scripts tests
git grep -n "load_race_entry_id_map" -- scripts tests
git grep -n "target_race_count" -- scripts tests

新規未追跡ファイルがgit grepに出ない場合は、rg等でworktreeも確認する。

期待結果:

    productionのRaceEntrySource定義は新規moduleだけ

    production具象Sourceは0件

    SQLite queryは0件

    Repository-backed Resolverは未実装

    productionへtarget_race_count追加なし

Git Safety

stage、commit、pushは禁止。

常に禁止:

git add .
git add -A
git commit -a
git clean
git reset
git restore
git stash
git commit --amend
git rebase
force push

次を操作・stage・commitしない。

database/keiba.db
logs/
logs/配下すべて

作業終了時に必ず実行する。

git diff --check
git status --short

Completion Report

作業完了後、docs/LATEST_CODEX_REPORT.mdを今回の結果で置き換える。

最低限、次を報告する。

    変更ファイル一覧

    Protocol配置

    最終class定義

    method最終signature

    keyword-only契約

    annotations

    戻り値annotation

    runtime_checkable使用有無

    public method一覧

    method本文

    Source mappingの意味

    import依存方向

    package export変更有無

    新例外追加有無

    追加したテスト内容

    専用テスト結果

    Resolver／Builder／Snapshot関連テスト結果

    Repository関連テスト結果

    全pytest結果

    git diff --check結果

    検索結果

    git status --short

    想定commit対象

    SQLite Source未実装

    Repository-backed Resolver未実装

    PersistedSimulationBetSource未実装

    Pipeline未接続

    database/keiba.dbとlogs/を操作していないこと

    stage・commit・push未実施

    blockerの有無

Stop Condition

以下の場合は作業を停止し、LATEST_CODEX_REPORT.mdへ報告する。

    設計書と実在contractが衝突する

    Allowed Files外の変更が必要

    Protocolだけでは成立せずschema変更が必要

    package exportに循環importが発生する

    テスト失敗の原因が今回の範囲外

    Git statusに想定外ファイルがある

    不明な既存挙動を推測する必要がある

実装・テスト・報告後は、stage・commit・pushせずレビュー待ちで停止する。
CURRENT_PHASE_clean.md
Current Phase
Status

READY_FOR_CODEX
Phase

Phase 4C-2d3b1e1
RaceEntrySource Protocol contract
Base Commit

86b87db
Branch

feature/ver0.8-simulator
Objective

Prediction側のhorse ID selectionを、race-scoped entry IDへ解決するための読取境界として、RaceEntrySource Protocolと専用契約テストを追加する。

今回はProtocol contractだけを実装する。

SQLite具象Source、Repository-backed Resolver、Builder接続、Snapshot Repository変更、Pipeline接続には進まない。
Allowed Files

変更可能なファイルは次だけとする。

scripts/simulation/race_entry_source.py
tests/test_race_entry_source_contract.py
docs/LATEST_CODEX_REPORT.md

Forbidden Files

次を変更しない。

database/keiba.db
logs/
logs/配下すべて
docs/CURRENT_PHASE.md
docs/VER0.8_SIMULATOR_DESIGN.md
AGENTS.md
scripts/simulation/selection_resolver.py
scripts/simulation/bet_plan_builder.py
scripts/simulation/bet_plan_snapshot.py
scripts/simulation/repositories/
scripts/migrations/
その他のproductionコード
その他のtests
schema
migration
CLI
settings

Required Contracts

正式なProtocol名:

RaceEntrySource

正式API:

from typing import Mapping, Protocol, Sequence


class RaceEntrySource(Protocol):
    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        ...

契約上の意味:

戻り値key   = requested prediction horse ID
戻り値value = 指定race内の正式race entry ID

BetRecommendation.horse_idsは現行モデルではhorses.id由来だが、Source境界ではrace所属と対応関係を明示的に解決する。

物理的に同じ整数値であっても、horse IDとrace entry IDを無検証で同一視しない。
Implementation Requirements

    typing.Protocolを使用する

    runtime_checkableを使用しない

    public methodはload_race_entry_id_mapだけ

    method本文は...だけ

    全引数をkeyword-onlyにする

    race_id annotationはint

    horse_ids annotationはSequence[int]

    戻り値annotationはMapping[int, int]

    default引数を追加しない

    *argsを追加しない

    **kwargsを追加しない

    asyncにしない

    concrete behaviorを追加しない

    validation処理を追加しない

    SQLを追加しない

    SQLiteをimportしない

    Repository例外をimportしない

    Stubやin-memory実装をproductionへ追加しない

    package root exportは既存の明示export規約がある場合だけ検討する

    exportによって循環importが起きる場合は直接module importとする

    新しい例外classを追加しない

Protocolが将来の具象Sourceへ要求する意味:

    1 selectionをbatchで解決する

    horse単位のN+1 queryを行わない

    SQL row順へ依存しない

    requested horse IDとの対応をmappingで返す

    missing IDを暗黙補完しない

    wrong-race IDを別raceから取得しない

    requested以外の余分なmappingを返さない

    duplicate resolutionを黙認しない

ただし、これらのruntime validationやDB処理は今回実装しない。
Validation and Error Handling

今回のProtocol moduleにはvalidation・例外処理を実装しない。

将来の正式分担:

Resolver:
- public API入力validation
- empty selection
- duplicate horse IDs
- Source戻り値contract
- missing／wrong-raceのValueError化
- 入力順でのtuple再構成

SQLite RaceEntrySource:
- connection利用条件
- batch query
- DB row型
- DB重複
- race所属
- RepositoryValidationError
- RepositoryDataIntegrityError

今回、新例外を定義・再定義しない。
Required Tests

専用テストで最低限、次を確認する。
Protocol構造

    RaceEntrySourceがProtocolである

    runtime-checkableではない

    public methodはload_race_entry_id_mapだけ

    method本文が宣言のみ

    concrete instance storageを持たない

    SQLやSQLite実装を持たない

Signature

    race_idがkeyword-only

    horse_idsがkeyword-only

    引数順が正式順

    defaultなし

    可変長引数なし

    asyncではない

    race_id: int

    horse_ids: Sequence[int]

    -> Mapping[int, int]

inspect.signature()およびtyping.get_type_hints()を既存テスト規約に従って使用する。
構造的適合

tests内だけに次の最小Stubを作成してよい。

class StubRaceEntrySource:
    def load_race_entry_id_map(
        self,
        *,
        race_id: int,
        horse_ids: Sequence[int],
    ) -> Mapping[int, int]:
        return {horse_id: horse_id for horse_id in horse_ids}

このStubはsignature確認専用であり、productionのidentity変換実装ではない。

確認:

    構造的にmethodを実装可能

    runtime isinstance判定は行わない

    productionへStubを追加しない

依存境界

Production moduleが次へ依存しないことを確認する。

sqlite3
database module
Repository具象実装
Repository例外
RaceEntrySelectionResolver具象実装
SimulationBetPlanBuilder
Snapshot Repository
Provider
PredictionPipeline
Simulator
Result
Summary
CLI
settings
HTTP
network
current time

回帰確認

最低限、以下を実行する。

tests/test_race_entry_source_contract.py
tests/test_race_entry_selection_resolver_contract.py
tests/test_simulation_bet_plan_builder.py
tests/test_simulation_bet_plan_snapshot.py
tests/test_simulation_bet_plan_snapshot_repository_contract.py
tests/test_sqlite_simulation_bet_plan_snapshot_repository.py

関連テスト後、全pytestを実行する。
Search Checks

最低限、次を確認する。

git grep -n "class RaceEntrySource" -- scripts tests
git grep -n "load_race_entry_id_map" -- scripts tests
git grep -n "target_race_count" -- scripts tests

新規未追跡ファイルがgit grepに出ない場合は、rg等でworktreeも確認する。

期待結果:

    productionのRaceEntrySource定義は新規moduleだけ

    production具象Sourceは0件

    SQLite queryは0件

    Repository-backed Resolverは未実装

    productionへtarget_race_count追加なし

Git Safety

stage、commit、pushは禁止。

常に禁止:

git add .
git add -A
git commit -a
git clean
git reset
git restore
git stash
git commit --amend
git rebase
force push

次を操作・stage・commitしない。

database/keiba.db
logs/
logs/配下すべて

作業終了時に必ず実行する。

git diff --check
git status --short

Completion Report

作業完了後、docs/LATEST_CODEX_REPORT.mdを今回の結果で置き換える。

最低限、次を報告する。

    変更ファイル一覧

    Protocol配置

    最終class定義

    method最終signature

    keyword-only契約

    annotations

    戻り値annotation

    runtime_checkable使用有無

    public method一覧

    method本文

    Source mappingの意味

    import依存方向

    package export変更有無

    新例外追加有無

    追加したテスト内容

    専用テスト結果

    Resolver／Builder／Snapshot関連テスト結果

    Repository関連テスト結果

    全pytest結果

    git diff --check結果

    検索結果

    git status --short

    想定commit対象

    SQLite Source未実装

    Repository-backed Resolver未実装

    PersistedSimulationBetSource未実装

    Pipeline未接続

    database/keiba.dbとlogs/を操作していないこと

    stage・commit・push未実施

    blockerの有無

Stop Condition

以下の場合は作業を停止し、LATEST_CODEX_REPORT.mdへ報告する。

    設計書と実在contractが衝突する

    Allowed Files外の変更が必要

    Protocolだけでは成立せずschema変更が必要

    package exportに循環importが発生する

    テスト失敗の原因が今回の範囲外

    Git statusに想定外ファイルがある

    不明な既存挙動を推測する必要がある

実装・テスト・報告後は、stage・commit・pushせずレビュー待ちで停止する。
