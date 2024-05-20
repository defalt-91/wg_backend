from typing import Generator, Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.Settings import get_settings

settings = get_settings()

engine = create_engine(
    url=settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    echo=False,
    future=True,
)

SessionFactory = sessionmaker(
    bind=engine, future=True, autoflush=True, autocommit=False, expire_on_commit=False
)


# Dependency
# def get_db(request: Request):
#     return request.state.db


def get_session() -> Generator:
    session = SessionFactory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    else:
        session.commit()
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_session)]


class SessionContextManager:
    def __init__(self):
        self.session = SessionFactory()

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()


# async def get_session2():
# 	with SessionContextManager() as session:
# 		yield session
