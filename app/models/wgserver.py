from sqlalchemy import Boolean, Column, Integer, String,Uuid,DateTime,DATETIME,TIMESTAMP,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import FunctionElement
from sqlalchemy.ext.compiler import compiles
import uuid
from app.db.registry import DateMixin, NameMixin,mapper_registry
# from app.models.client import Client

@mapper_registry.mapped
class WGServer(DateMixin,NameMixin):
	id = Column(Integer,primary_key=True,index=True,nullable=False,autoincrement=True,unique=True)
	privateKey = Column(String(255),nullable=False,)
	publicKey = Column(String(255),nullable=False,)
	address = Column(String(255),nullable=False,)
	clients = relationship(
     "Client",
		back_populates="server",
		single_parent=True,
		cascade="all, delete, delete-orphan",
  		# passive_deletes=True,
	)