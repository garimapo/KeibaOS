"""Historical input snapshot schema migration."""

import sqlite3


VERSION = 10
NAME = "v010_historical_input_snapshot_schema"


STATEMENTS = (
    """CREATE TABLE historical_input_source_identities (
        organization TEXT NOT NULL CHECK (typeof(organization) = 'text' AND organization <> ''),
        source_system TEXT NOT NULL CHECK (typeof(source_system) = 'text' AND source_system <> ''),
        PRIMARY KEY (organization, source_system)
    ) WITHOUT ROWID""",
    """CREATE TABLE historical_input_external_races (
        organization TEXT NOT NULL,
        source_system TEXT NOT NULL,
        external_race_id TEXT NOT NULL CHECK (typeof(external_race_id) = 'text' AND external_race_id <> ''),
        internal_race_id INTEGER NOT NULL CHECK (typeof(internal_race_id) = 'integer' AND internal_race_id > 0),
        PRIMARY KEY (organization, source_system, external_race_id),
        UNIQUE (organization, source_system, external_race_id, internal_race_id),
        UNIQUE (organization, source_system, internal_race_id),
        FOREIGN KEY (organization, source_system)
            REFERENCES historical_input_source_identities (organization, source_system)
            ON DELETE RESTRICT ON UPDATE RESTRICT,
        FOREIGN KEY (internal_race_id)
            REFERENCES races (id)
            ON DELETE RESTRICT ON UPDATE RESTRICT
    ) WITHOUT ROWID""",
    """CREATE TABLE historical_input_external_entries (
        organization TEXT NOT NULL,
        source_system TEXT NOT NULL,
        external_race_id TEXT NOT NULL,
        external_entry_id TEXT NOT NULL CHECK (typeof(external_entry_id) = 'text' AND external_entry_id <> ''),
        internal_race_id INTEGER NOT NULL CHECK (typeof(internal_race_id) = 'integer' AND internal_race_id > 0),
        race_entry_id INTEGER NOT NULL CHECK (typeof(race_entry_id) = 'integer' AND race_entry_id > 0),
        PRIMARY KEY (organization, source_system, external_race_id, external_entry_id),
        UNIQUE (organization, source_system, internal_race_id, race_entry_id),
        FOREIGN KEY (organization, source_system, external_race_id, internal_race_id)
            REFERENCES historical_input_external_races
                (organization, source_system, external_race_id, internal_race_id)
            ON DELETE RESTRICT ON UPDATE RESTRICT,
        FOREIGN KEY (internal_race_id, race_entry_id)
            REFERENCES horses (race_id, id)
            ON DELETE RESTRICT ON UPDATE RESTRICT
    ) WITHOUT ROWID""",
    """CREATE TABLE historical_input_snapshots (
        snapshot_id INTEGER PRIMARY KEY,
        dataset_id TEXT NOT NULL CHECK (typeof(dataset_id) = 'text' AND dataset_id <> ''),
        organization TEXT NOT NULL,
        source_system TEXT NOT NULL,
        external_race_id TEXT NOT NULL,
        internal_race_id INTEGER NOT NULL CHECK (typeof(internal_race_id) = 'integer' AND internal_race_id > 0),
        source_url TEXT NULL CHECK (source_url IS NULL OR (typeof(source_url) = 'text' AND source_url <> '')),
        captured_at_utc TEXT NOT NULL CHECK (
            typeof(captured_at_utc) = 'text' AND length(captured_at_utc) = 32
            AND substr(captured_at_utc, 11, 1) = 'T'
            AND substr(captured_at_utc, 20, 1) = '.'
            AND substr(captured_at_utc, -6) = '+00:00'
            AND captured_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
        ),
        information_cutoff_utc TEXT NOT NULL CHECK (
            typeof(information_cutoff_utc) = 'text' AND length(information_cutoff_utc) = 32
            AND substr(information_cutoff_utc, 11, 1) = 'T'
            AND substr(information_cutoff_utc, 20, 1) = '.'
            AND substr(information_cutoff_utc, -6) = '+00:00'
            AND information_cutoff_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
        ),
        content_sha256 TEXT NOT NULL CHECK (
            typeof(content_sha256) = 'text' AND length(content_sha256) = 64
            AND content_sha256 NOT GLOB '*[^0-9a-f]*'
        ),
        UNIQUE (dataset_id, organization, source_system, external_race_id, captured_at_utc),
        FOREIGN KEY (organization, source_system, external_race_id, internal_race_id)
            REFERENCES historical_input_external_races
                (organization, source_system, external_race_id, internal_race_id)
            ON DELETE RESTRICT ON UPDATE RESTRICT,
        FOREIGN KEY (internal_race_id)
            REFERENCES races (id)
            ON DELETE RESTRICT ON UPDATE RESTRICT
    )""",
    """CREATE TABLE historical_input_snapshot_races (
        snapshot_id INTEGER PRIMARY KEY,
        target_race_date TEXT NOT NULL CHECK (
            typeof(target_race_date) = 'text' AND length(target_race_date) = 10
            AND target_race_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        ),
        scheduled_start_at_utc TEXT NOT NULL CHECK (
            typeof(scheduled_start_at_utc) = 'text' AND length(scheduled_start_at_utc) = 32
            AND substr(scheduled_start_at_utc, 11, 1) = 'T'
            AND substr(scheduled_start_at_utc, 20, 1) = '.'
            AND substr(scheduled_start_at_utc, -6) = '+00:00'
            AND scheduled_start_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
        ),
        place TEXT NOT NULL CHECK (typeof(place) = 'text' AND place <> ''),
        distance_m INTEGER NOT NULL CHECK (typeof(distance_m) = 'integer' AND distance_m > 0),
        track TEXT NOT NULL CHECK (typeof(track) = 'text' AND track <> ''),
        track_condition TEXT NOT NULL CHECK (typeof(track_condition) = 'text' AND track_condition <> ''),
        race_name TEXT NULL CHECK (race_name IS NULL OR (typeof(race_name) = 'text' AND race_name <> '')),
        race_class TEXT NULL CHECK (race_class IS NULL OR (typeof(race_class) = 'text' AND race_class <> '')),
        weather TEXT NULL CHECK (weather IS NULL OR (typeof(weather) = 'text' AND weather <> '')),
        FOREIGN KEY (snapshot_id)
            REFERENCES historical_input_snapshots (snapshot_id)
            ON DELETE RESTRICT ON UPDATE RESTRICT
    )""",
    """CREATE TABLE historical_input_snapshot_entries (
        snapshot_id INTEGER NOT NULL,
        race_entry_id INTEGER NOT NULL CHECK (typeof(race_entry_id) = 'integer' AND race_entry_id > 0),
        external_entry_id TEXT NOT NULL CHECK (typeof(external_entry_id) = 'text' AND external_entry_id <> ''),
        external_horse_id TEXT NULL CHECK (external_horse_id IS NULL OR (typeof(external_horse_id) = 'text' AND external_horse_id <> '')),
        horse_no INTEGER NOT NULL CHECK (typeof(horse_no) = 'integer' AND horse_no > 0),
        jockey TEXT NOT NULL CHECK (typeof(jockey) = 'text' AND jockey <> ''),
        win_odds_text TEXT NOT NULL CHECK (typeof(win_odds_text) = 'text' AND win_odds_text <> ''),
        entry_order INTEGER NOT NULL CHECK (typeof(entry_order) = 'integer' AND entry_order >= 0),
        PRIMARY KEY (snapshot_id, race_entry_id),
        UNIQUE (snapshot_id, external_entry_id),
        UNIQUE (snapshot_id, horse_no),
        UNIQUE (snapshot_id, entry_order),
        FOREIGN KEY (snapshot_id)
            REFERENCES historical_input_snapshots (snapshot_id)
            ON DELETE RESTRICT ON UPDATE RESTRICT
    ) WITHOUT ROWID""",
    """CREATE TABLE historical_input_snapshot_past_races (
        snapshot_id INTEGER NOT NULL,
        race_entry_id INTEGER NOT NULL CHECK (typeof(race_entry_id) = 'integer' AND race_entry_id > 0),
        past_race_index INTEGER NOT NULL CHECK (typeof(past_race_index) = 'integer' AND past_race_index >= 0),
        race_date TEXT NOT NULL CHECK (
            typeof(race_date) = 'text' AND length(race_date) = 10
            AND race_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        ),
        place TEXT NOT NULL CHECK (typeof(place) = 'text' AND place <> ''),
        race_name TEXT NOT NULL CHECK (typeof(race_name) = 'text' AND race_name <> ''),
        race_class TEXT NOT NULL CHECK (typeof(race_class) = 'text' AND race_class <> ''),
        distance_m INTEGER NOT NULL CHECK (typeof(distance_m) = 'integer' AND distance_m > 0),
        track TEXT NOT NULL CHECK (typeof(track) = 'text' AND track <> ''),
        weather TEXT NOT NULL CHECK (typeof(weather) = 'text' AND weather <> ''),
        track_condition TEXT NOT NULL CHECK (typeof(track_condition) = 'text' AND track_condition <> ''),
        finish INTEGER NOT NULL CHECK (typeof(finish) = 'integer' AND finish > 0),
        margin_text TEXT NOT NULL CHECK (typeof(margin_text) = 'text' AND margin_text <> ''),
        race_time TEXT NOT NULL CHECK (typeof(race_time) = 'text' AND race_time <> ''),
        weight_text TEXT NOT NULL CHECK (typeof(weight_text) = 'text' AND weight_text <> ''),
        weight_diff_text TEXT NOT NULL CHECK (typeof(weight_diff_text) = 'text' AND weight_diff_text <> ''),
        jockey TEXT NOT NULL CHECK (typeof(jockey) = 'text' AND jockey <> ''),
        popularity INTEGER NOT NULL CHECK (typeof(popularity) = 'integer' AND popularity >= 0),
        odds_text TEXT NOT NULL CHECK (typeof(odds_text) = 'text' AND odds_text <> ''),
        passing_order TEXT NOT NULL CHECK (typeof(passing_order) = 'text'),
        fourth_corner_position INTEGER NOT NULL CHECK (
            typeof(fourth_corner_position) = 'integer' AND fourth_corner_position >= 0
        ),
        PRIMARY KEY (snapshot_id, race_entry_id, past_race_index),
        FOREIGN KEY (snapshot_id, race_entry_id)
            REFERENCES historical_input_snapshot_entries (snapshot_id, race_entry_id)
            ON DELETE RESTRICT ON UPDATE RESTRICT
    ) WITHOUT ROWID""",
    """CREATE TABLE historical_input_snapshot_provenance (
        snapshot_id INTEGER NOT NULL,
        input_type TEXT NOT NULL CHECK (input_type IN ('track', 'entry', 'odds', 'jockey', 'past_race')),
        audit_key TEXT NOT NULL CHECK (typeof(audit_key) = 'text' AND audit_key <> ''),
        source TEXT NOT NULL CHECK (typeof(source) = 'text' AND source <> ''),
        source_id TEXT NOT NULL CHECK (typeof(source_id) = 'text' AND source_id <> ''),
        race_entry_id INTEGER NULL CHECK (
            race_entry_id IS NULL OR (typeof(race_entry_id) = 'integer' AND race_entry_id > 0)
        ),
        available_at_utc TEXT NULL CHECK (
            available_at_utc IS NULL OR (
                typeof(available_at_utc) = 'text' AND length(available_at_utc) = 32
                AND substr(available_at_utc, 11, 1) = 'T'
                AND substr(available_at_utc, 20, 1) = '.'
                AND substr(available_at_utc, -6) = '+00:00'
                AND available_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
            )
        ),
        observed_at_utc TEXT NULL CHECK (
            observed_at_utc IS NULL OR (
                typeof(observed_at_utc) = 'text' AND length(observed_at_utc) = 32
                AND substr(observed_at_utc, 11, 1) = 'T'
                AND substr(observed_at_utc, 20, 1) = '.'
                AND substr(observed_at_utc, -6) = '+00:00'
                AND observed_at_utc GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]+00:00'
            )
        ),
        past_race_index INTEGER NULL CHECK (
            past_race_index IS NULL OR (typeof(past_race_index) = 'integer' AND past_race_index >= 0)
        ),
        PRIMARY KEY (snapshot_id, audit_key),
        CHECK (available_at_utc IS NOT NULL OR observed_at_utc IS NOT NULL),
        CHECK (
            (input_type = 'track' AND race_entry_id IS NULL AND past_race_index IS NULL)
            OR (input_type IN ('entry', 'odds', 'jockey') AND race_entry_id IS NOT NULL AND past_race_index IS NULL)
            OR (input_type = 'past_race' AND race_entry_id IS NOT NULL)
        ),
        FOREIGN KEY (snapshot_id)
            REFERENCES historical_input_snapshots (snapshot_id)
            ON DELETE RESTRICT ON UPDATE RESTRICT,
        FOREIGN KEY (snapshot_id, race_entry_id)
            REFERENCES historical_input_snapshot_entries (snapshot_id, race_entry_id)
            ON DELETE RESTRICT ON UPDATE RESTRICT,
        FOREIGN KEY (snapshot_id, race_entry_id, past_race_index)
            REFERENCES historical_input_snapshot_past_races (snapshot_id, race_entry_id, past_race_index)
            ON DELETE RESTRICT ON UPDATE RESTRICT
    ) WITHOUT ROWID""",
)


INDEXES = (
    "CREATE UNIQUE INDEX ux_horses_race_id_id ON horses (race_id, id)",
    "CREATE INDEX idx_his_external_races_internal ON historical_input_external_races (internal_race_id, organization, source_system)",
    "CREATE INDEX idx_his_external_entries_internal ON historical_input_external_entries (internal_race_id, race_entry_id, organization, source_system)",
    """CREATE INDEX idx_his_snapshots_latest_eligible
        ON historical_input_snapshots (
            dataset_id,
            internal_race_id,
            organization,
            source_system,
            external_race_id,
            captured_at_utc DESC
        )""",
)


TRIGGERS = (
    """CREATE TRIGGER trg_his_snapshot_entry_mapping_insert
        BEFORE INSERT ON historical_input_snapshot_entries
        FOR EACH ROW
        WHEN NOT EXISTS (
            SELECT 1
            FROM historical_input_snapshots AS s
            JOIN historical_input_external_entries AS e
              ON e.organization = s.organization
             AND e.source_system = s.source_system
             AND e.external_race_id = s.external_race_id
             AND e.internal_race_id = s.internal_race_id
             AND e.external_entry_id = NEW.external_entry_id
             AND e.race_entry_id = NEW.race_entry_id
            WHERE s.snapshot_id = NEW.snapshot_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'historical snapshot entry mapping mismatch');
        END""",
    """CREATE TRIGGER trg_his_snapshot_entry_mapping_update
        BEFORE UPDATE OF snapshot_id, external_entry_id, race_entry_id
        ON historical_input_snapshot_entries
        FOR EACH ROW
        WHEN NOT EXISTS (
            SELECT 1
            FROM historical_input_snapshots AS s
            JOIN historical_input_external_entries AS e
              ON e.organization = s.organization
             AND e.source_system = s.source_system
             AND e.external_race_id = s.external_race_id
             AND e.internal_race_id = s.internal_race_id
             AND e.external_entry_id = NEW.external_entry_id
             AND e.race_entry_id = NEW.race_entry_id
            WHERE s.snapshot_id = NEW.snapshot_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'historical snapshot entry mapping mismatch');
        END""",
    """CREATE TRIGGER trg_his_snapshot_header_mapping_update
        BEFORE UPDATE OF organization, source_system, external_race_id, internal_race_id
        ON historical_input_snapshots
        FOR EACH ROW
        WHEN EXISTS (
            SELECT 1
            FROM historical_input_snapshot_entries AS se
            WHERE se.snapshot_id = OLD.snapshot_id
              AND NOT EXISTS (
                  SELECT 1
                  FROM historical_input_external_entries AS e
                  WHERE e.organization = NEW.organization
                    AND e.source_system = NEW.source_system
                    AND e.external_race_id = NEW.external_race_id
                    AND e.internal_race_id = NEW.internal_race_id
                    AND e.external_entry_id = se.external_entry_id
                    AND e.race_entry_id = se.race_entry_id
              )
        )
        BEGIN
            SELECT RAISE(ABORT, 'historical snapshot header mapping mismatch');
        END""",
    """CREATE TRIGGER trg_his_external_entry_referenced_update
        BEFORE UPDATE OF organization, source_system, external_race_id, external_entry_id, internal_race_id, race_entry_id
        ON historical_input_external_entries
        FOR EACH ROW
        WHEN EXISTS (
            SELECT 1
            FROM historical_input_snapshots AS s
            JOIN historical_input_snapshot_entries AS se
              ON se.snapshot_id = s.snapshot_id
            WHERE s.organization = OLD.organization
              AND s.source_system = OLD.source_system
              AND s.external_race_id = OLD.external_race_id
              AND s.internal_race_id = OLD.internal_race_id
              AND se.external_entry_id = OLD.external_entry_id
              AND se.race_entry_id = OLD.race_entry_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'referenced historical external entry is immutable');
        END""",
    """CREATE TRIGGER trg_his_external_entry_referenced_delete
        BEFORE DELETE ON historical_input_external_entries
        FOR EACH ROW
        WHEN EXISTS (
            SELECT 1
            FROM historical_input_snapshots AS s
            JOIN historical_input_snapshot_entries AS se
              ON se.snapshot_id = s.snapshot_id
            WHERE s.organization = OLD.organization
              AND s.source_system = OLD.source_system
              AND s.external_race_id = OLD.external_race_id
              AND s.internal_race_id = OLD.internal_race_id
              AND se.external_entry_id = OLD.external_entry_id
              AND se.race_entry_id = OLD.race_entry_id
        )
        BEGIN
            SELECT RAISE(ABORT, 'referenced historical external entry cannot be deleted');
        END""",
)


def apply(connection: sqlite3.Connection) -> None:
    for statement in STATEMENTS + INDEXES + TRIGGERS:
        connection.execute(statement)
