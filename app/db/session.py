from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Generator,AsyncGenerator
from fastapi import Request
from app.core.Settings import get_settings
settings=get_settings()

engine = create_engine(
	url=settings.SQLALCHEMY_DATABASE_URL,
	pool_pre_ping=True,
	echo=False,
	future=True,
)

SessionFactory = sessionmaker(
	bind=engine,
	future=True,
	autoflush=True,
	autocommit=False,
	expire_on_commit=False
)

# Dependency
# def get_db(request: Request):
#     return request.state.db

def get_session() -> Generator:
	session = SessionFactory()
	try:
		yield session
	except:
		session.rollback()
		raise
	else:
		session.commit()
	finally:
		session.close()


# class SessionContextManager:
# 	def __init__(self):
# 		self.session = SessionFactory()
	
# 	def __enter__(self):
# 		return self.session
	
# 	def __exit__(self, exc_type, exc_val, exc_tb):
# 		self.session.close()


# async def get_session2():
# 	with SessionContextManager() as session:
# 		yield session