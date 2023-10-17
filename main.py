import logging
from datetime import datetime
from typing import List

import databases
import sqlalchemy
from fastapi import FastAPI
from pydantic import BaseModel

# Настройки базы данных
DATABASE_URL = "sqlite:///DB.db"
database = databases.Database(DATABASE_URL)
metadata = sqlalchemy.MetaData()
engine = sqlalchemy.create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Создаем таблицы
users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("f_name", sqlalchemy.String(32)),
    sqlalchemy.Column("l_name", sqlalchemy.String(32)),
    sqlalchemy.Column("email", sqlalchemy.String(128)),
    sqlalchemy.Column("password", sqlalchemy.String(128)),
)

orders = sqlalchemy.Table(
    "orders",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("user_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id")),
    sqlalchemy.Column("product_id", sqlalchemy.Integer, sqlalchemy.ForeignKey("products.id")),
    sqlalchemy.Column("order_date", sqlalchemy.DateTime, default=datetime.utcnow),
    sqlalchemy.Column("status", sqlalchemy.String, default="pending"),
)

products = sqlalchemy.Table(
    "products",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(32)),
    sqlalchemy.Column("description", sqlalchemy.String(128)),
    sqlalchemy.Column("price", sqlalchemy.Float),
)

# Создаем таблицы
metadata.create_all(engine)

# Логгер
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем приложение
app = FastAPI()


@app.on_event("startup")
async def startup():
    logger.info("Starting up...")
    await database.connect()
    logger.info("Database connection established.")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down...")
    await database.disconnect()
    logger.info("Database connection closed.")


class UserModel(BaseModel):
    """модель нужна для создания пользователя"""
    f_name: str
    l_name: str
    email: str
    password: str


class User(BaseModel):
    """модель нужна для возврата данных о пользователе из БД клиенту"""
    id: int
    f_name: str
    l_name: str
    email: str
    password: str


class OrderCreate(BaseModel):
    """модель нужна для создания заказа"""
    user_id: int
    product_id: int


class Order(BaseModel):
    """модель нужна для отображения заказа"""
    id: int
    user_id: int
    product_id: int


class ProductCreate(BaseModel):
    """модель нужна для создания продукта"""
    name: str
    description: str
    price: float


class Product(ProductCreate):
    """модель нужна для возврата данных о продукте из БД клиенту"""
    id: int
    name: str
    description: str
    price: float


@app.post("/users/", response_model=User)
async def create_user(user: UserModel):
    """Создание нового пользователя"""
    query = users.insert().values(
        f_name=user.f_name,
        l_name=user.l_name,
        email=user.email,
        password=user.password,
    )
    last_id = await database.execute(query)
    logger.info(f'Пользователь {user.email} создан.')
    return {**user.dict(), "id": last_id}


@app.get("/users/", response_model=List[User])
async def read_users():
    """Получение всех пользователей"""
    query = users.select()
    logger.info('Пользователи получены.')
    return await database.fetch_all(query)


@app.get("/orders/", response_model=List[Order])
async def read_orders():
    """Получение всех заказов"""
    query = orders.select()
    logger.info('Заказы получены.')
    return await database.fetch_all(query)


@app.post("/orders/", response_model=Order)
async def create_order(order: OrderCreate):
    """Создание нового заказа"""
    query = orders.insert().values(
        user_id=order.user_id,
        product_id=order.product_id,
        order_date=datetime.utcnow(),
    )
    record_id = await database.execute(query)
    logger.info(f'Заказ {order.product_id} создан.')
    return {**order.dict(), "id": record_id}


@app.get("/products/", response_model=List[Product])
async def read_products():
    """Получение всех продуктов"""
    query = products.select()
    logger.info('Продукты получены.')
    return await database.fetch_all(query)


@app.post("/products/", response_model=Product)
async def create_product(product: ProductCreate):
    """Создание нового продукта"""
    query = products.insert().values(
        name=product.name,
        description=product.description,
        price=product.price,
    )
    await database.execute(query)
    logger.info(f'Продукт {product.name} создан.')
    return {**product.dict()}
