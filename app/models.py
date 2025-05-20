from sqlalchemy import Column, Integer, String, DateTime
from app.db import Base
from datetime import datetime

class Car(Base):
    __tablename__ = "cars"

    url = Column(String, primary_key=True, index=True)
    title = Column(String)
    price_usd = Column(Integer)
    odometer = Column(Integer)
    username = Column(String)
    phone_number = Column(String)
    image_url = Column(String, nullable=True)
    images_count = Column(Integer)
    car_number = Column(String, nullable=True)
    car_vin = Column(String, nullable=True)
    datetime_found = Column(DateTime, default=datetime.utcnow)
