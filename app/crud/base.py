from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging
from app.api import exceptions

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        db.add(db_obj)
        # db.flush()
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_object_or_404(
            self, session: Session, instance_id: int
    ) -> Optional[ModelType]:
        orm_object = session.get(self.model, instance_id)
        if not orm_object:
            raise exceptions.not_found_error()
        return orm_object

    def get(self, db: Session, item_id: Any) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == item_id).first()

    def get_multi(
            self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> Optional[List[ModelType]]:
        object_list = db.query(self.model).offset(skip).limit(limit).all()
        if not object_list:
            raise exceptions.client_not_found()
        return object_list

    def update(
            self,
            db: Session,
            *,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]],
            db_obj: ModelType,
    ) -> Optional[ModelType]:
        if not db_obj:
            raise exceptions.not_found_error()
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        obj_data = jsonable_encoder(db_obj)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        # db.flush()
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, item_id: int) -> ModelType:
        obj = db.query(self.model).get(item_id)
        if not obj:
            raise exceptions.not_found_error()
        db.delete(obj)
        # db.flush()
        return obj

    def save(self, session: Session, obj: ModelType) -> ModelType:
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj
