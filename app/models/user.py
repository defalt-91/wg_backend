from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.registry import DateMixin, NameMixin,mapper_registry

@mapper_registry.mapped
class User(DateMixin,NameMixin):
    __tablename__='user'
    id = Column(Integer, primary_key=True, index=True,autoincrement=True,unique=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=True)
    # items = relationship("Item", back_populates="owner")
    def __repr__(self):
        return f"<{self.__class__.__name__}, id={self.id}>"

    def __str__(self):
        return self.__repr__()

    __mapper_args__ = {"always_refresh": True}