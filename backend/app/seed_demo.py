from database.db import Base, engine, SessionLocal
from models.payment import Payment
from agents.recovery_agent import analyze_payment

Base.metadata.create_all(bind=engine)

db = SessionLocal()


def create_payment(
    customer_id,
    amount,
    payment_method,
    failure_reason,
    retry_count,
    recovery_status,
):
    analysis = analyze_payment(
        failure_reason,
        retry_count,
        amount,
        0,
    )

    return Payment(
        customer_id=customer_id,
        amount=amount,
        payment_method=payment_method,
        failure_reason=failure_reason,
        retry_count=retry_count,
        recovery_action=analysis["recovery_action"],
        customer_message=analysis["customer_message"],
        risk_score=analysis["risk_score"],
        priority=analysis["priority"],
        recovery_status=recovery_status,
        decision_explanation=analysis["decision_explanation"],
    )


try:
    existing_count = db.query(Payment).count()

    if existing_count > 0:
        print(f"Database already contains {existing_count} payment records.")
        print("No demo data was inserted.")

    else:
        # Six pending failed payments.
        pending_payments = [
            {
                "customer_id": "CUST001",
                "amount": 2500,
                "payment_method": "card",
                "failure_reason": "insufficient funds",
                "retry_count": 1,
            },
            {
                "customer_id": "CUST003",
                "amount": 5000,
                "payment_method": "upi",
                "failure_reason": "insufficient funds",
                "retry_count": 0,
            },
            {
                "customer_id": "CUST006",
                "amount": 4000,
                "payment_method": "card",
                "failure_reason": "network timeout",
                "retry_count": 0,
            },
            {
                "customer_id": "CUST007",
                "amount": 2500,
                "payment_method": "upi",
                "failure_reason": "declined",
                "retry_count": 0,
            },
            {
                "customer_id": "CUST010",
                "amount": 6000,
                "payment_method": "card",
                "failure_reason": "network timeout",
                "retry_count": 2,
            },
            {
                "customer_id": "CUST012",
                "amount": 3000,
                "payment_method": "upi",
                "failure_reason": "declined",
                "retry_count": 0,
            },
        ]

        for payment_data in pending_payments:
            payment = create_payment(
                customer_id=payment_data["customer_id"],
                amount=payment_data["amount"],
                payment_method=payment_data["payment_method"],
                failure_reason=payment_data["failure_reason"],
                retry_count=payment_data["retry_count"],
                recovery_status="pending",
            )

            db.add(payment)

        # Ten recovered payments.
        # Their failure reasons are intentionally varied so that
        # the demo reproduces the current recovery-action distribution:
        #
        # 2 send_payment_link
        # 6 retry_payment
        # 1 request_new_payment_method
        # 1 manual_review
        recovered_payments = [
            {
                "customer_id": "CUST101",
                "amount": 3000,
                "payment_method": "card",
                "failure_reason": "insufficient funds",
            },
            {
                "customer_id": "CUST102",
                "amount": 3500,
                "payment_method": "upi",
                "failure_reason": "insufficient funds",
            },
            {
                "customer_id": "CUST103",
                "amount": 4000,
                "payment_method": "card",
                "failure_reason": "declined",
            },
            {
                "customer_id": "CUST104",
                "amount": 4500,
                "payment_method": "upi",
                "failure_reason": "declined",
            },
            {
                "customer_id": "CUST105",
                "amount": 5000,
                "payment_method": "card",
                "failure_reason": "declined",
            },
            {
                "customer_id": "CUST106",
                "amount": 3000,
                "payment_method": "upi",
                "failure_reason": "declined",
            },
            {
                "customer_id": "CUST107",
                "amount": 3500,
                "payment_method": "card",
                "failure_reason": "declined",
            },
            {
                "customer_id": "CUST108",
                "amount": 4000,
                "payment_method": "upi",
                "failure_reason": "declined",
            },
            {
                "customer_id": "CUST109",
                "amount": 5000,
                "payment_method": "card",
                "failure_reason": "expired",
            },
            {
                "customer_id": "CUST110",
                "amount": 5500,
                "payment_method": "upi",
                "failure_reason": "unknown issue",
            },
        ]

        for payment_data in recovered_payments:
            payment = create_payment(
                customer_id=payment_data["customer_id"],
                amount=payment_data["amount"],
                payment_method=payment_data["payment_method"],
                failure_reason=payment_data["failure_reason"],
                retry_count=0,
                recovery_status="success",
            )

            db.add(payment)

        db.commit()

        total_records = db.query(Payment).count()

        print("Demo data inserted successfully.")
        print(f"Total payment records: {total_records}")

finally:
    db.close()