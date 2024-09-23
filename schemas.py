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

class ProductCreate(ProductBase):
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
