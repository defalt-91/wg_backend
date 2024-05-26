import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

from wg_backend.api import exceptions

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound = BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound = BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        logging.basicConfig(level = logging.INFO)
        self.logger = logging.getLogger(__name__)

    def create(self, session: Session, *, obj_in: CreateSchemaType) -> ModelType | None:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # type: ignore
        return self.save(session = session, obj = db_obj)

    def get_object_or_404(
            self, session: Session, instance_id: int
    ) -> Optional[ModelType]:
        orm_object = session.get(self.model, instance_id)
        if not orm_object:
            raise exceptions.not_found_error()
        return orm_object

    def get(self, session: Session, item_id: Any) -> Optional[ModelType]:
        return session.query(self.model).filter(self.model.id == item_id).first()

    def get_multi(
            self, session: Session, *, skip: int = 0, limit: int = 100
    ) -> Optional[List[ModelType]]:
        object_list = session.query(self.model).offset(skip).limit(limit).all()
        if not object_list:
            raise exceptions.peer_not_found()
        return object_list

    def update(
            self,
            session: Session,
            *,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]],
            db_obj: ModelType,
    ) -> Optional[ModelType]:
        if not db_obj:
            raise exceptions.not_found_error()
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset = True)
        obj_data = jsonable_encoder(db_obj)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        return self.save(session = session, obj = db_obj)

    def remove(self, session: Session, *, item_id: int) -> ModelType:
        obj = session.query(self.model).get(item_id)
        if not obj:
            raise exceptions.not_found_error()
        session.delete(obj)
        session.commit()
        return obj

    def save(self, session: Session, obj: ModelType) -> ModelType:
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj
