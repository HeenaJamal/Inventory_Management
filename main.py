from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, Column, Integer, String, DECIMAL, ForeignKey, Enum, TIMESTAMP
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from pydantic import BaseModel
from datetime import datetime
import os

DATABASE_URL = "mysql+mysqlconnector://root:Arhaanjamal@localhost/inventory_management"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI()

# Models
class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(255), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    stock = Column(Integer, nullable=False)

class Supplier(Base):
    __tablename__ = "suppliers"
    supplier_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50), nullable=False)

class Order(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer, nullable=False)
    ordered_at = Column(TIMESTAMP, default=datetime.utcnow)
    delivered_at = Column(TIMESTAMP, nullable=True)
    status = Column(Enum('pending', 'delivered'), default='pending')

    product = relationship("Product")

Base.metadata.create_all(bind=engine)

# Pydantic Schemas
class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    stock: int

class OrderCreate(BaseModel):
    product_id: int
    quantity: int

# API Endpoints
@app.post("/products/", response_model=ProductCreate)
def create_product(product: ProductCreate):
    db = SessionLocal()
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    db.close()
    return db_product

@app.get("/products/{product_id}", response_model=ProductCreate)
def read_product(product_id: int):
    db = SessionLocal()
    product = db.query(Product).filter(Product.product_id == product_id).first()
    db.close()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@app.post("/orders/", response_model=OrderCreate)
def create_order(order: OrderCreate):
    db = SessionLocal()
    product = db.query(Product).filter(Product.product_id == order.product_id).first()
    if not product or product.stock < order.quantity:
        db.close()
        raise HTTPException(status_code=400, detail="Insufficient stock or product not found")
    
    db_order = Order(**order.dict())
    product.stock -= order.quantity  # Reduce stock
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    db.close()
    return db_order

@app.get("/orders/")
def list_orders():
    db = SessionLocal()
    orders = db.query(Order).all()
    db.close()
    return orders
