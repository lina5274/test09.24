from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PythonEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()
engine = create_engine("postgresql://user:password@localhost/dbname")

class OrderStatus(PythonEnum):
    IN_PROGRESS = "в процессе"
    SENT = "отправлен"
    DELIVERED = "доставлен"

class ProductModel(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float, index=True)
    quantity = Column(Integer)

class OrderModel(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    creation_date = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum(OrderStatus))

class OrderItemModel(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer)
    order = relationship("OrderModel", back_populates="items")
    product = relationship("ProductModel")
