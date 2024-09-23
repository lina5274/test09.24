from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import uuid
from models import ProductModel, OrderModel, OrderItemModel, OrderStatus
from schemas import ProductCreate, Product, OrderCreate, Order, OrderItemCreate, OrderItem

app = FastAPI()

# Настройка SQLAlchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

Base = declarative_base()
engine = create_engine("postgresql://user:password@localhost/dbname")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)


# Регистрация эндпоинтов для продуктов
@app.post("/products/", response_model=Product)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = ProductModel(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@app.get("/products/", response_model=List[Product])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(ProductModel).offset(skip).limit(limit).all()
    return products


@app.get("/products/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/products/{product_id}", response_model=Product)
def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id)
    if db_product.first() is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db_product.update(product.dict())
    db.commit()
    return db_product.first()


@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id)
    if db_product.first() is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product.first())
    db.commit()
    return {"message": "Product deleted successfully"}


# Регистрация эндпоинтов для заказов
from sqlalchemy.orm import Session


@app.post("/orders/", response_model=Order)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    # Проверка наличия товара на складе
    order_items = order.items
    for item in order_items:
        product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
        if product.quantity < item.quantity:
            raise HTTPException(status_code=400, detail=f"Not enough quantity of product {item.product_id}")

    # Создание заказа и элементов заказа
    order_db = OrderModel(**order.dict())
    db.add(order_db)
    db.commit()
    db.refresh(order_db)

    for item in order_items:
        order_item_db = OrderItemModel(
            id=str(uuid.uuid4()),
            order_id=order_db.id,
            product_id=item.product_id,
            quantity=item.quantity
        )
        db.add(order_item_db)
        db.commit()
        db.refresh(order_item_db)

        # Обновление количества товара на складе
        product = db.query(ProductModel).filter(ProductModel.id == item.product_id).first()
        product.quantity -= item.quantity
        db.commit()

    return order_db


@app.get("/orders/", response_model=List[Order])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = db.query(OrderModel).offset(skip).limit(limit).all()
    return orders


@app.get("/orders/{order_id}", response_model=Order)
def read_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.patch("/orders/{order_id}/status", response_model=Order)
def update_order_status(order_id: int, status: OrderStatus, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status
    db.commit()
    return order
