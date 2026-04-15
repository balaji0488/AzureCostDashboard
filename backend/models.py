from sqlalchemy import Column, Integer, String, Float, Date
from database import Base

class CostRecord(Base):
    __tablename__ = 'cost_records'
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    subscription_id = Column(String, index=True)
    resource_group = Column(String, index=True)
    service_name = Column(String, index=True)
    location = Column(String, index=True)
    pretax_cost = Column(Float)
    currency = Column(String)

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    subscription_id = Column(String, primary_key=True)
    display_name = Column(String)

