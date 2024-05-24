from sqlalchemy.orm import registry, declarative_mixin, declared_attr
from sqlalchemy import Column, func
from sqlalchemy.sql.sqltypes import DateTime, Integer, TIMESTAMP
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import expression


mapper_registry = registry()


class utcnow(expression.FunctionElement):
    type = DateTime()
    inherit_cache = True


@compiles(utcnow, "postgresql")
def pg_utcnow(element, compiler, **kw):
    return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


@compiles(utcnow, "mssql")
def ms_utcnow(element, compiler, **kw):
    return "GETUTCDATE()"


@declarative_mixin
class DateMixin:
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=None,
        server_default=func.now(),
        index=True,
        nullable=False,
        doc="Time of creation",
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=None,
        onupdate=func.now(),
        index=True,
        nullable=True,
        doc="Time of last update",
    )


@declarative_mixin
class NameMixin:
    id = Column(
        Integer,
        primary_key=True,
        index=True,
        nullable=False,
        autoincrement=True,
        unique=True,
    )

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def __repr__(self):
        return f"<{self.__class__.__name__}, id={self.id}>"

    def __str__(self):
        return self.__repr__()

    __mapper_args__ = {"always_refresh": True}
