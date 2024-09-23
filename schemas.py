from pydantic import BaseModel
from datetime import datetime
from enum import Enum as PythonEnum

class OrderStatus(PythonEnum):
    IN_PROGRESS = "в процессе"
    SENT = "отправлен"
    DELIVERED = "доставлен"

class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    quantity: int

class ProductCreafrom pydantic import BaseModel, Field
from typing import List
from models import OrderStatus
from datetime import datetime


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    quantity: int

class Product(ProductCreate):
    id: int

class OrderCreate(BaseModel):
    products: List[ProductCreate]

class Order(OrderCreate):
    id: int
    creation_date: datetime
    status: OrderStatus

class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    quantity: int | None = None
te(ProductBase):
    pass

class Product(ProductBase):
    id: int

class OrderBase(BaseModel):
    status: OrderStatus

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    creation_date: datetime
    items: list["OrderItem"] = []

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int

class OrderItem(OrderItemBase):
    id: int
    order: Order

class OrderItemCreate(OrderItemBase):
    pass
