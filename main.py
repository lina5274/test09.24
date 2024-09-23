import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from fastapi import FastAPI, HTTPException, Depends, Body
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import List
from models import ProductModel, OrderModel, OrderStatus
from schemas import ProductCreate, Product, OrderCreate, Order, ProductUpdate
from functools import wraps


# Инициализация FastAPI приложения
app = FastAPI()

# Настройка SQLAlchemy
Base = declarative_base()
db_url = "postgresql://user:password@localhost/dbname"
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Функция для создания базы данных, если она не существует
def create_database_if_not_exists():
    # Подключаемся к PostgreSQL (в базу postgres, чтобы иметь возможность создать новую базу)
    conn = psycopg2.connect(dbname='postgres', user='user', password='password', host='localhost')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    # Имя базы данных
    dbname = "dbname"

    # Проверяем, существует ли база данных
    cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}'")
    exists = cursor.fetchone()

    # Если база данных не существует, создаем её
    if not exists:
        cursor.execute(f"CREATE DATABASE {dbname}")
        print(f"База данных '{dbname}' успешно создана")
    else:
        print(f"База данных '{dbname}' уже существует")

    cursor.close()
    conn.close()

# Получение сессии для работы с базой данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Создание базы данных и таблиц при запуске приложения
@app.on_event("startup")
async def startup_event():
    # Создаем базу данных, если она не существует
    create_database_if_not_exists()

    # Создаем таблицы, если они не существуют
    Base.metadata.create_all(bind=engine)

# Декоратор для проверки наличия товара
def validate_inventory(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        if isinstance(result, dict) and "items" in result:
            for item in result["items"]:
                product = db.query(ProductModel).filter(ProductModel.id == item["product_id"]).first()
                if product.quantity - item["quantity"] < 0:
                    raise HTTPException(status_code=400, detail=f"Not enough inventory for product {item['product_id']}")
        return result
    return wrapper

# Эндпоинты для товаров
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

@app.get("/products/{id}", response_model=Product)
def read_product(id: int, db: Session = Depends(get_db)):
    product = db.query(ProductModel).filter(ProductModel.id == id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/products/{id}", response_model=Product)
def update_product(id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    existing_product = db.query(ProductModel).filter(ProductModel.id == id).first()
    if existing_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    existing_product.name = product.name
    existing_product.description = product.description
    existing_product.price = product.price
    existing_product.quantity = product.quantity

    db.commit()
    db.refresh(existing_product)
    return existing_product


@app.delete("/products/{id}", response_model=Product)
def delete_product(id: int, db: Session = Depends(get_db)):
    product = db.query(ProductModel).filter(ProductModel.id == id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return product

# Эндпоинты для заказов
@app.post("/orders/", response_model=Order)
@validate_inventory
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    db_order = OrderModel(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

@app.get("/orders/", response_model=List[Order])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    orders = db.query(OrderModel).offset(skip).limit(limit).all()
    return orders

@app.get("/orders/{id}", response_model=Order)
def read_order(id: int, db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.patch("/orders/{id}/status", response_model=Order)
def update_order_status(id: int, status: OrderStatus = Body(...), db: Session = Depends(get_db)):
    order = db.query(OrderModel).filter(OrderModel.id == id).first()
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = status.value
    db.commit()
    db.refresh(order)
    return order
