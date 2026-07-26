# KeibaOS Codex Working Agreement

## 役割と作業順

- ChatGPTは設計、レビュー、QA、フェーズ管理を担当する。
- Codexは実装、テスト、差分確認、作業報告を担当する。
- 作業順は、設計、実装、レビュー、明示的commit承認、push、次フェーズとする。
- Codexは`docs/CURRENT_PHASE.md`に記載された範囲だけを実施する。
- 作業後は`docs/LATEST_CODEX_REPORT.md`を更新して停止する。

## 変更範囲と契約

- `Allowed Files`以外を変更しない。
- 設計書と実在contractが衝突した場合は実装を停止して報告する。
- 既存domain contractを都合よく変更しない。
- テストを通すためだけのproduction APIを追加しない。
- 詳細な設計判断の正本は`docs/VER0.8_SIMULATOR_DESIGN.md`とする。

## Git安全ルール

明示的承認がない限り、stage、commit、pushを行わない。常に次を禁止する。

```text
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
```

stageする場合は、承認されたファイルを個別指定する。次をstage・commitしない。

```text
database/keiba.db
logs/
logs/配下すべて
```

通常の最終dirty状態として、次を許容する。

```text
 M database/keiba.db
?? logs/
```

## KeibaOS固有契約

- `SimulationSummary.race_count`を正式fieldとして維持し、`target_race_count`を追加しない。
- Engine → Predictor → Value → Generator → Strategy → Pipeline → CLIの責務分離を維持する。
- prediction cutoffとsettlement cutoffを混同せず、prediction時点より後のsettlement時刻を理由に拒否しない。
- allocationのrecommendation件数・順序・object identityを無断変更しない。
- recommendation rankとpurchase orderを混同しない。
- horse IDとrace entry IDを無検証で同一視しない。
- Repositoryは保存データを自動修復せず、immutable Snapshotをsilent overwriteしない。

## テストと確認

作業終了時に必ず実行する。

```text
git diff --check
git status --short
```

`docs/CURRENT_PHASE.md`に指定された専用テスト、関連テスト、全pytest、検索確認を実行する。未実行のテストは未実行と明記し、失敗を隠したり成功扱いにしない。

## 停止条件

次の場合は変更を続けず停止して報告する。

- 設計書と実装contractが衝突する。
- Allowed Files外の変更が必要になる。
- schema／migration変更が別フェーズとして必要になる。
- 不明な既存挙動を推測する必要がある。
- テスト失敗原因が今回の範囲外である。
- Git statusに想定外ファイルがある。
- commit承認が必要である。
