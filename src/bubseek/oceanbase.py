"""Register pyobvector SQLAlchemy dialect for OceanBase/SeekDB compatibility."""

from __future__ import annotations

import pymysql
import pyobvector  # noqa: F401
from bub import hookimpl
from pyobvector.schema.dialect import OceanBaseDialect as _OceanBaseDialect
from sqlalchemy.dialects import registry


def _is_savepoint_not_exist(exc: BaseException) -> bool:
    """Check if exception is MySQL 1305 (savepoint does not exist)."""
    if isinstance(exc, pymysql.err.OperationalError) and exc.args and exc.args[0] == 1305:
        return True
    orig = getattr(exc, "orig", None)
    if orig is not None and orig is not exc:
        return _is_savepoint_not_exist(orig)
    return False


class OceanBaseDialect(_OceanBaseDialect):
    """OceanBase dialect that tolerates missing savepoints.

    OceanBase/SeekDB may implicitly release savepoints on errors (e.g. deadlock,
    failed DML). When SQLAlchemy later tries RELEASE SAVEPOINT or ROLLBACK TO
    SAVEPOINT, it gets (1305, 'savepoint does not exist'). We catch and ignore
    that to avoid masking the original error.
    """

    def do_release_savepoint(self, connection, name: str) -> None:
        try:
            super().do_release_savepoint(connection, name)
        except Exception as e:
            if not _is_savepoint_not_exist(e):
                raise

    def do_rollback_to_savepoint(self, connection, name: str) -> None:
        try:
            super().do_rollback_to_savepoint(connection, name)
        except Exception as e:
            if not _is_savepoint_not_exist(e):
                raise


registry.register("mysql.oceanbase", "bubseek.oceanbase", "OceanBaseDialect")


def register(framework: object) -> object:
    """Bub plugin entry point. Registers dialect only."""
    return _OceanBaseDialectPlugin()


class _OceanBaseDialectPlugin:
    """Minimal plugin to satisfy Bub loader. Dialect already registered at import."""

    @hookimpl
    def provide_tape_store(self) -> None:
        """Skip; let bub_tapestore_sqlalchemy provide the store."""
        return None
