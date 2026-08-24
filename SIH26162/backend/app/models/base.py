"""
SIH26162 — SQLAlchemy Declarative Base.

Defines the declarative base class, common timestamp mixins,
and dialect compilation handlers for PostgreSQL + PostGIS with SQLite testing compatibility.
"""

from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.compiler import compiles

# ---------------------------------------------------------------------------
# GeoAlchemy2 SQLite Compatibility Hook for Non-PostGIS Test Environments
# ---------------------------------------------------------------------------
try:
    from geoalchemy2.types import _GISType
    import geoalchemy2.admin.dialects.sqlite as _sqlite_admin
    from geoalchemy2 import functions as _gafunc

    # Compile GIS geometry column type as TEXT on SQLite
    @compiles(_GISType, "sqlite")
    def _compile_gis_type_sqlite(type_, compiler, **kw):
        return "TEXT"

    # Disable SpatiaLite C-extension function triggers on pure SQLite
    _sqlite_admin.before_create = lambda *args, **kwargs: None
    _sqlite_admin.after_create = lambda *args, **kwargs: None

    # Handle result processing on SQLite without binary hex errors
    _orig_result_processor = _GISType.result_processor
    _GISType.result_processor = lambda self, dialect, coltype: (
        (lambda value: value) if (dialect and dialect.name == "sqlite") else _orig_result_processor(self, dialect, coltype)
    )

    # Compile PostGIS functions to pass-through on SQLite
    for _fn_cls in [
        _gafunc.ST_GeomFromEWKT,
        _gafunc.ST_GeomFromText,
        _gafunc.ST_AsEWKB,
        _gafunc.ST_AsText,
        _gafunc.ST_GeomFromEWKB,
    ]:
        @compiles(_fn_cls, "sqlite")
        def _compile_gis_func(element, compiler, **kw):
            clauses = list(element.clauses)
            if clauses:
                return compiler.process(clauses[0], **kw)
            return "NULL"

except ImportError:
    pass


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class TimestampMixin:
    """Mixin adding created_at and updated_at timestamps."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
