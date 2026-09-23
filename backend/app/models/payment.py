from sqlalchemy import Column, Integer, String, Float
from database.db import Base


class Payment(Base):

    __tablename__ = "payments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    customer_id = Column(
        String,
        index=True
    )

    amount = Column(
        Float
    )

    payment_method = Column(
        String
    )

    failure_reason = Column(
        String
    )

    retry_count = Column(
        Integer,
        default=0
    )

    recovery_action = Column(
        String
    )

    customer_message = Column(
        String
    )

    risk_score = Column(
        Integer
    )

    priority = Column(
        String
    )

    recovery_status = Column(
        String,
        default="pending"
    )

    decision_explanation = Column(
        String
    )