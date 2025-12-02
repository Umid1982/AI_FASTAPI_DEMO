from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.database.connection import Base
import structlog

logger = structlog.get_logger()

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T], ABC):
    """Base repository class with common CRUD operations."""
    
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
    
    def create(self, obj_in: Dict[str, Any]) -> T:
        """Create a new record."""
        try:
            db_obj = self.model(**obj_in)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            logger.debug("Created record", model=self.model.__name__, id=getattr(db_obj, 'id', None))
            return db_obj
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to create record", model=self.model.__name__, error=str(e))
            raise
    
    def get(self, id: Any) -> Optional[T]:
        """Get record by ID."""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first()
        except Exception as e:
            logger.error("Failed to get record", model=self.model.__name__, id=id, error=str(e))
            raise
    
    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get multiple records with pagination and filters."""
        try:
            query = self.db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, key).in_(value))
                        else:
                            query = query.filter(getattr(self.model, key) == value)
            
            return query.offset(skip).limit(limit).all()
        except Exception as e:
            logger.error("Failed to get multiple records", model=self.model.__name__, error=str(e))
            raise
    
    def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[T]:
        """Update record by ID."""
        try:
            db_obj = self.get(id)
            if not db_obj:
                return None
            
            for key, value in obj_in.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            
            self.db.commit()
            self.db.refresh(db_obj)
            logger.debug("Updated record", model=self.model.__name__, id=id)
            return db_obj
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to update record", model=self.model.__name__, id=id, error=str(e))
            raise
    
    def delete(self, id: Any) -> bool:
        """Delete record by ID."""
        try:
            db_obj = self.get(id)
            if not db_obj:
                return False
            
            self.db.delete(db_obj)
            self.db.commit()
            logger.debug("Deleted record", model=self.model.__name__, id=id)
            return True
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to delete record", model=self.model.__name__, id=id, error=str(e))
            raise
    
    def exists(self, id: Any) -> bool:
        """Check if record exists."""
        try:
            return self.db.query(self.model).filter(self.model.id == id).first() is not None
        except Exception as e:
            logger.error("Failed to check existence", model=self.model.__name__, id=id, error=str(e))
            raise
    
    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filters."""
        try:
            query = self.db.query(self.model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        if isinstance(value, list):
                            query = query.filter(getattr(self.model, key).in_(value))
                        else:
                            query = query.filter(getattr(self.model, key) == value)
            
            return query.count()
        except Exception as e:
            logger.error("Failed to count records", model=self.model.__name__, error=str(e))
            raise
    
    def get_by_field(self, field: str, value: Any) -> Optional[T]:
        """Get record by field value."""
        try:
            if not hasattr(self.model, field):
                raise ValueError(f"Field {field} does not exist on {self.model.__name__}")
            
            return self.db.query(self.model).filter(getattr(self.model, field) == value).first()
        except Exception as e:
            logger.error("Failed to get by field", model=self.model.__name__, field=field, value=value, error=str(e))
            raise
    
    def get_multi_by_field(
        self,
        field: str,
        value: Any,
        skip: int = 0,
        limit: int = 100
    ) -> List[T]:
        """Get multiple records by field value."""
        try:
            if not hasattr(self.model, field):
                raise ValueError(f"Field {field} does not exist on {self.model.__name__}")
            
            return (
                self.db.query(self.model)
                .filter(getattr(self.model, field) == value)
                .offset(skip)
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error("Failed to get multiple by field", model=self.model.__name__, field=field, value=value, error=str(e))
            raise
