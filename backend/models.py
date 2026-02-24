from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()


class FinOrder(Base):
    __tablename__ = "tblfinorder"

    id = Column("ID", Integer, primary_key=True)
    name = Column("OrderName", String(255))
    status = Column("Status", String(50))
    created_at = Column("CreateDate", DateTime)
