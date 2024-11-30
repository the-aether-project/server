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
from sqlalchemy import DDL, event
from sqlalchemy.ext.declarative import declarative_base


def DB_Table():
    Base = declarative_base(metadata=MetaData())

    class Users(Base):
        __tablename__ = "users"
        id = Column(Integer, primary_key=True, autoincrement=True)
        username = Column(String(100), unique=False, nullable=False)
        email = Column(String(255), unique=True, nullable=False)
        stored_credentials = Column(String(255), nullable=False)
        is_landlord = Column(Boolean, default=False)
        created_at = Column(TIMESTAMP, server_default=func.now())

    class Computers(Base):
        __tablename__ = "computers"
        id = Column(Integer, primary_key=True, autoincrement=True)
        rate = Column(Integer, CheckConstraint("rate >= 0"), nullable=False)
        landlord_id = Column(
            Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        )

        created_at = Column(TIMESTAMP, server_default=func.now())

    class Transactions(Base):
        __tablename__ = "transactions"
        id = Column(Integer, primary_key=True, autoincrement=True)
        starttime = Column(TIMESTAMP, nullable=False)
        endtime = Column(TIMESTAMP)
        customer_id = Column(
            Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
        )
        landlord_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
        computer_id = Column(Integer, ForeignKey("computers.id", ondelete="SET NULL"))
        total_cost = Column(Integer, default=0)
        created_at = Column(TIMESTAMP, server_default=func.now())

    drop_total_cost_fn = DDL("""
        DROP FUNCTION IF EXISTS calculate_total_cost CASCADE;
    """)
    calculate_total_cost = DDL("""
        CREATE OR REPLACE FUNCTION calculate_total_cost() 
        RETURNS TRIGGER AS $$
        DECLARE
            computer_rate INT;
        BEGIN
            SELECT rate INTO computer_rate FROM computers WHERE id = NEW.computer_id;
            IF NEW.endtime IS NOT NULL AND NEW.starttime IS NOT NULL THEN
                NEW.total_cost := EXTRACT(EPOCH FROM (NEW.endtime - NEW.starttime)) / 3600 * computer_rate;
            ELSE
                NEW.total_cost := NULL;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    update_total_cost = DDL("""
        CREATE TRIGGER update_total_cost
        BEFORE UPDATE OF endtime ON transactions
        FOR EACH ROW
        WHEN (NEW.endtime IS DISTINCT FROM OLD.endtime)
        EXECUTE FUNCTION calculate_total_cost();
    """)

    event.listen(Base.metadata, "after_create", drop_total_cost_fn)
    event.listen(Base.metadata, "after_create", calculate_total_cost)
    event.listen(Base.metadata, "after_create", update_total_cost)

    return Base
