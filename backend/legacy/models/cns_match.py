from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from datetime import datetime
from app.db import Base


class CNSDatabase(Base):
    __tablename__ = "cns_databases"
    
    id = Column(String, primary_key=True)  # e.g., "ofac_sdn"
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    description = Column(Text)
    country = Column(String)
    last_updated = Column(DateTime)
    record_count = Column(Integer, default=0)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class CNSMatch(Base):
    __tablename__ = "cns_matches"
    
    id = Column(String, primary_key=True)  # e.g., "CNS-12345"
    name = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    source = Column(String, nullable=False)
    database_id = Column(String, nullable=False)
    list_type = Column(String)  # SANCTIONS, WATCHLIST
    entity_type = Column(String)  # INDIVIDUAL, ENTITY
    country = Column(String)
    date_of_birth = Column(String, nullable=True)
    aka_names = Column(JSON, nullable=True)  # Array of alternative names
    added_date = Column(String)
    program = Column(String)
    remarks = Column(Text)
    risk_level = Column(String)  # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime, default=datetime.utcnow)
