"""Explicit no-network composition bootstrap; source/capability already established."""
from scripts.simulation import nar_pre_c_operational_envelope_archive_migration as schema


def bootstrap_nar_pre_c_operational_envelope_archive(*, runner, capability):
    capability.require_current_owner(runner)
    connection = schema.base._connection(runner._connection)
    if connection.in_transaction:
        raise RuntimeError("Phase108 bootstrap requires idle locked connection")
    objects = schema.base._objects(connection)
    if objects == schema.parent_ddl() | schema._DDL:
        schema.require_nar_pre_c_operational_envelope_archive_schema(connection)
        return
    schema.attempt.require_nar_operational_timing_attempt_archive_schema(connection)
    if connection.execute(f"SELECT 1 FROM {schema.attempt.ATTEMPTS} WHERE claim_identity=?", (capability.claim_identity,)).fetchone():
        raise RuntimeError("Phase108 installation must precede this claim's first attempt")
    connection.execute("BEGIN IMMEDIATE")
    try:
        for statement in schema._DDL.values():
            connection.execute(statement)
        connection.execute(f"INSERT INTO {schema.REGISTRY} VALUES(?,?)", (schema.VERSION, schema.NAME))
        schema.require_nar_pre_c_operational_envelope_archive_schema(connection)
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
