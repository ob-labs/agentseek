from __future__ import annotations

import pymysql
import pyobvector  # noqa: F401
from pyobvector.schema.dialect import OceanBaseDialect as _OceanBaseDialect
from sqlalchemy.dialects import registry


def _is_savepoint_not_exist(exc: BaseException) -> bool:
    if isinstance(exc, pymysql.err.OperationalError) and exc.args and exc.args[0] == 1305:
        return True
    orig = getattr(exc, "orig", None)
    if orig is not None and orig is not exc:
        return _is_savepoint_not_exist(orig)
    return False


class OceanBaseDialect(_OceanBaseDialect):
    supports_statement_cache = True

    def do_release_savepoint(self, connection, name: str) -> None:
        try:
            super().do_release_savepoint(connection, name)
        except Exception as exc:
            if not _is_savepoint_not_exist(exc):
                raise

    def do_rollback_to_savepoint(self, connection, name: str) -> None:
        try:
            super().do_rollback_to_savepoint(connection, name)
        except Exception as exc:
            if not _is_savepoint_not_exist(exc):
                raise


def register_oceanbase_dialect() -> None:
    registry.register(
        "mysql.oceanbase",
        "agentseek_tapestore_oceanbase.oceanbase",
        "OceanBaseDialect",
    )
