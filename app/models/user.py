from sqlalchemy import Boolean, Column, String
from app.db.registry import DateMixin, NameMixin, mapper_registry


@mapper_registry.mapped
class User(DateMixin, NameMixin):
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=lambda: True)
    is_superuser = Column(Boolean(), default=lambda: False)
    client_id = Column(String(255), nullable=True, unique=True)
    client_secret = Column(String(255), nullable=True, )
    scope = Column(String(255), nullable=True)
