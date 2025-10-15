"""
Database models using SQLAlchemy ORM.
Each class represents a table in the SQLite database.
"""

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# Base class for all models
Base = declarative_base()

def generate_id():
    """Generate unique ID for records"""
    return str(uuid.uuid4())


class Artisan(Base):
    """
    Stores artisan (user) information
    """
    __tablename__ = "artisans"
    
    id = Column(String, primary_key=True, default=generate_id)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=True)
    location = Column(String)
    city = Column(String)
    state = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    material_requests = relationship("MaterialRequest", back_populates="artisan")
    orders = relationship("Order", back_populates="artisan")
    micro_stores = relationship("MicroStore", back_populates="artisan")


class MaterialRequest(Base):
    """
    Stores material requests from artisans
    This is what IntakeAgent creates
    """
    __tablename__ = "material_requests"
    
    id = Column(String, primary_key=True, default=generate_id)
    artisan_id = Column(String, ForeignKey("artisans.id"), nullable=False)
    
    # Request details
    material = Column(String, nullable=False)  # e.g., "cement", "bricks"
    quantity = Column(Float, nullable=False)   # e.g., 100 (kg or units)
    unit = Column(String, default="kg")        # e.g., "kg", "pieces"
    budget = Column(Float, nullable=False)     # in rupees
    timeline = Column(String)                  # e.g., "next week", "2 days"
    
    # Status tracking
    status = Column(String, default="pending")  # pending, quoted, ordered, delivered, cancelled
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    artisan = relationship("Artisan", back_populates="material_requests")
    quotes = relationship("SupplierQuote", back_populates="material_request")


class Supplier(Base):
    """
    Stores supplier information
    """
    __tablename__ = "suppliers"
    
    id = Column(String, primary_key=True, default=generate_id)
    name = Column(String, nullable=False)
    phone = Column(String)
    email = Column(String)
    
    # Location
    address = Column(Text)
    city = Column(String)
    state = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    delivery_radius_km = Column(Float, default=50)
    
    # Business details
    materials = Column(JSON)  # List of materials they supply: ["cement", "bricks"]
    rating = Column(Float, default=3.0)
    total_reviews = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quotes = relationship("SupplierQuote", back_populates="supplier")


class SupplierQuote(Base):
    """
    Stores quotes from suppliers for material requests
    SupplierAgent creates these
    """
    __tablename__ = "supplier_quotes"
    
    id = Column(String, primary_key=True, default=generate_id)
    request_id = Column(String, ForeignKey("material_requests.id"), nullable=False)
    supplier_id = Column(String, ForeignKey("suppliers.id"), nullable=False)
    
    # Quote details
    price_per_unit = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    delivery_charge = Column(Float, default=0)
    delivery_days = Column(Integer, default=3)
    
    # Selection
    selected = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    material_request = relationship("MaterialRequest", back_populates="quotes")
    supplier = relationship("Supplier", back_populates="quotes")


class Order(Base):
    """
    Stores confirmed orders
    CommitAgent creates these after quote selection
    """
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True, default=generate_id)
    artisan_id = Column(String, ForeignKey("artisans.id"), nullable=False)
    request_id = Column(String, ForeignKey("material_requests.id"), nullable=False)
    quote_id = Column(String, ForeignKey("supplier_quotes.id"), nullable=False)
    
    # Payment details
    total_amount = Column(Float, nullable=False)
    upi_link = Column(String)
    payment_status = Column(String, default="pending")  # pending, completed, failed
    
    # Order documents
    po_path = Column(String)  # Path to PDF purchase order
    
    # Status
    status = Column(String, default="confirmed")  # confirmed, in_transit, delivered, cancelled
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)
    
    # Relationships
    artisan = relationship("Artisan", back_populates="orders")


class MicroStore(Base):
    """
    Stores micro-store (product listing) information
    SalesAgent creates these
    """
    __tablename__ = "micro_stores"
    
    id = Column(String, primary_key=True, default=generate_id)
    artisan_id = Column(String, ForeignKey("artisans.id"), nullable=False)
    
    # Product details
    product_name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    
    # Media
    image_path = Column(String)
    qr_code_path = Column(String)
    
    # Store URL
    store_url = Column(String, unique=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    views = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    artisan = relationship("Artisan", back_populates="micro_stores")


class Ledger(Base):
    """
    Stores all financial transactions
    CashAgent manages these
    """
    __tablename__ = "ledger"
    
    id = Column(String, primary_key=True, default=generate_id)
    artisan_id = Column(String, ForeignKey("artisans.id"), nullable=False)
    order_id = Column(String, ForeignKey("orders.id"), nullable=True)
    
    # Transaction details
    type = Column(String, nullable=False)  # debit, credit
    amount = Column(Float, nullable=False)
    description = Column(Text)
    category = Column(String)  # material_purchase, sale, delivery_fee
    
    # Balance tracking
    balance_after = Column(Float)  # Balance after this transaction
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow)
