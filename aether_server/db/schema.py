from sqlalchemy import (
    Column,
    Integer,
    String,
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    func,
    ForeignKey,
    MetaData,
)
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base(metadata=MetaData())


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    username = Column(String(100), unique=False, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    stored_credentials = Column(String(255), nullable=False)
    is_landlord = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Computers(Base):
    __tablename__ = "computers"
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    rate = Column(Integer, CheckConstraint("rate >= 0"), nullable=False)
    landlord_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(TIMESTAMP, server_default=func.now())


class Transactions(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    starttime = Column(TIMESTAMP, nullable=False)
    endtime = Column(TIMESTAMP)
    customer_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    landlord_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    computer_id = Column(Integer, ForeignKey("computers.id", ondelete="SET NULL"))
    total_cost = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
