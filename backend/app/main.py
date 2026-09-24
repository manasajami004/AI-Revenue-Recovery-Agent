from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from schemas.payment import PaymentRequest
from agents.recovery_agent import analyze_payment

from database.db import get_db, Base, engine
from models.payment import Payment


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="AI Revenue Recovery Agent",
    description="AI agent for analyzing failed payments and recommending recovery actions.",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
	"https://ai-revenue-recovery-agent-1.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "AI Revenue Recovery Agent is running"
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# =========================================================
# ANALYZE PAYMENT
# =========================================================

@app.post("/api/analyze-payment")
def analyze_payment_api(
    payment: PaymentRequest,
    db: Session = Depends(get_db)
):

    # Count only currently active failed/pending payments
    # for this customer.
    previous_failures = db.query(Payment).filter(
        Payment.customer_id == payment.customer_id,
        Payment.recovery_status.in_(["pending", "failed"])
    ).count()


    # Send payment information to recovery agent
    result = analyze_payment(
        failure_reason=payment.failure_reason,
        retry_count=payment.retry_count,
        amount=payment.amount,
        previous_failures=previous_failures
    )


    # Create database record
    payment_record = Payment(
        customer_id=payment.customer_id,
        amount=payment.amount,
        payment_method=payment.payment_method,
        failure_reason=payment.failure_reason,
        retry_count=payment.retry_count,
        recovery_action=result["recovery_action"],
        customer_message=result["customer_message"],
        risk_score=result["risk_score"],
        priority=result["priority"],
        recovery_status="pending",
        decision_explanation=result["decision_explanation"]
    )


    # Save record
    db.add(payment_record)
    db.commit()
    db.refresh(payment_record)


    return {
        "id": payment_record.id,
        "customer_id": payment.customer_id,
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "failure_reason": payment.failure_reason,
        "recovery_action": result["recovery_action"],
        "customer_message": result["customer_message"],
        "retry_count": payment.retry_count,
        "risk_score": result["risk_score"],
        "priority": result["priority"],
        "previous_failures": previous_failures,
        "decision_explanation": result["decision_explanation"],
        "recovery_status": payment_record.recovery_status,
        "database_status": "saved"
    }


# =========================================================
# GET ALL PAYMENTS
# =========================================================

@app.get("/api/payments")
def get_payments(
    db: Session = Depends(get_db)
):

    payments = db.query(Payment).all()

    return {
        "total_payments": len(payments),
        "payments": payments
    }


# =========================================================
# RECOVERY PRIORITY QUEUE
# =========================================================

@app.get("/api/recovery-priority")
def get_recovery_priority(
    db: Session = Depends(get_db)
):

    # Only pending payments belong in the recovery queue
    payments = db.query(Payment).filter(
        Payment.recovery_status == "pending"
    ).all()


    # Priority ranking
    priority_order = {
        "high": 3,
        "medium": 2,
        "low": 1
    }


    # Sort:
    # 1. Priority
    # 2. Risk score
    # 3. Payment amount
    payments.sort(
        key=lambda payment: (
            priority_order.get(
                payment.priority,
                0
            ),
            payment.risk_score,
            payment.amount
        ),
        reverse=True
    )


    return {
        "total_pending_payments": len(payments),

        "priority_queue": [

            {
                "id": payment.id,
                "customer_id": payment.customer_id,
                "amount": payment.amount,
                "failure_reason": payment.failure_reason,
                "risk_score": payment.risk_score,
                "priority": payment.priority,
                "recovery_action": payment.recovery_action,
                "customer_message": payment.customer_message,
                "retry_count": payment.retry_count,
                "recovery_status": payment.recovery_status,
                "decision_explanation": payment.decision_explanation
            }

            for payment in payments
        ]
    }


# =========================================================
# DASHBOARD
# =========================================================

@app.get("/api/dashboard")
def get_dashboard(
    db: Session = Depends(get_db)
):

    payments = db.query(Payment).all()


    # -----------------------------------------------------
    # ACTIVE FAILED PAYMENTS
    # -----------------------------------------------------

    active_failed_payments = [
        payment
        for payment in payments
        if payment.recovery_status in ["pending", "failed"]
    ]


    total_failed_payments = len(
        active_failed_payments
    )


    total_amount_at_risk = sum(
        payment.amount
        for payment in active_failed_payments
    )


    # -----------------------------------------------------
    # RISK COUNTS
    # -----------------------------------------------------

    high_risk_payments = sum(
        1
        for payment in active_failed_payments
        if payment.priority == "high"
    )


    medium_risk_payments = sum(
        1
        for payment in active_failed_payments
        if payment.priority == "medium"
    )


    low_risk_payments = sum(
        1
        for payment in active_failed_payments
        if payment.priority == "low"
    )


    # -----------------------------------------------------
    # RECOVERY ACTIONS
    # -----------------------------------------------------

    recovery_actions = {}


    for payment in payments:

        action = payment.recovery_action

        if action not in recovery_actions:
            recovery_actions[action] = 0

        recovery_actions[action] += 1


    # -----------------------------------------------------
    # RECOVERY STATUS
    # -----------------------------------------------------

    recovered_payments = sum(
        1
        for payment in payments
        if payment.recovery_status == "success"
    )


    pending_recovery = sum(
        1
        for payment in payments
        if payment.recovery_status == "pending"
    )


    failed_recovery = sum(
        1
        for payment in payments
        if payment.recovery_status == "failed"
    )


    # -----------------------------------------------------
    # REVENUE
    # -----------------------------------------------------

    revenue_recovered = sum(
        payment.amount
        for payment in payments
        if payment.recovery_status == "success"
    )


    revenue_still_at_risk = sum(
        payment.amount
        for payment in payments
        if payment.recovery_status == "pending"
    )


    # -----------------------------------------------------
    # RECOVERY SUCCESS RATE
    # -----------------------------------------------------

    completed_recoveries = (
        recovered_payments +
        failed_recovery
    )


    if completed_recoveries > 0:

        recovery_success_rate = (
            recovered_payments /
            completed_recoveries
        ) * 100

    else:

        recovery_success_rate = 0


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "total_failed_payments":
            total_failed_payments,

        "total_amount_at_risk":
            total_amount_at_risk,

        "high_risk_payments":
            high_risk_payments,

        "medium_risk_payments":
            medium_risk_payments,

        "low_risk_payments":
            low_risk_payments,

        "recovery_actions":
            recovery_actions,

        "recovered_payments":
            recovered_payments,

        "revenue_recovered":
            revenue_recovered,

        "pending_recovery":
            pending_recovery,

        "failed_recovery":
            failed_recovery,

        "revenue_still_at_risk":
            revenue_still_at_risk,

        "recovery_success_rate":
            round(
                recovery_success_rate,
                2
            )
    }


# =========================================================
# CUSTOMER PROFILE
# =========================================================

@app.get("/api/customer/{customer_id}")
def get_customer_profile(
    customer_id: str,
    db: Session = Depends(get_db)
):

    payments = db.query(Payment).filter(
        Payment.customer_id == customer_id
    ).order_by(Payment.id.asc()).all()


    # Only pending and failed payments count as
    # current active failed payments
    failed_payments = [
        payment
        for payment in payments
        if payment.recovery_status in [
            "pending",
            "failed"
        ]
    ]


    previous_failed_payments = len(
        failed_payments
    )


    total_amount_at_risk = sum(
        payment.amount
        for payment in failed_payments
    )


    # -----------------------------------------------------
    # NO ACTIVE FAILED PAYMENTS
    # -----------------------------------------------------

    if not failed_payments:

        return {

            "customer_id":
                customer_id,

            "previous_failed_payments":
                0,

            "total_amount_at_risk":
                0,

            "risk_level":
                "low",

            "recommended_action":
                "no_recovery_needed",

            "payment_history": [

                {
                    "id":
                        payment.id,

                    "amount":
                        payment.amount,

                    "failure_reason":
                        payment.failure_reason,

                    "recovery_status":
                        payment.recovery_status,

                    "recovery_action":
                        payment.recovery_action
                }

                for payment in payments
            ]
        }


    # -----------------------------------------------------
    # FIND HIGHEST-RISK ACTIVE PAYMENT
    # -----------------------------------------------------

    highest_risk = max(
        failed_payments,
        key=lambda payment: payment.risk_score
    )


    return {

        "customer_id":
            customer_id,

        "previous_failed_payments":
            previous_failed_payments,

        "total_amount_at_risk":
            total_amount_at_risk,

        "risk_level":
            highest_risk.priority,

        "recommended_action":
            highest_risk.recovery_action,

        "payment_history": [

            {
                "id":
                    payment.id,

                "amount":
                    payment.amount,

                "failure_reason":
                    payment.failure_reason,

                "recovery_status":
                    payment.recovery_status,

                "recovery_action":
                    payment.recovery_action
            }

            for payment in payments
        ]
    }


# =========================================================
# SIMULATED RECOVERY ACTION
# =========================================================

@app.post("/api/payments/{payment_id}/recover")
def start_recovery_action(
    payment_id: int,
    db: Session = Depends(get_db)
):

    # Find payment
    payment = db.query(Payment).filter(
        Payment.id == payment_id
    ).first()


    # Payment not found
    if payment is None:

        return {
            "error": "Payment not found"
        }


    # Recovery already completed
    if payment.recovery_status != "pending":

        return {

            "payment_id":
                payment.id,

            "customer_id":
                payment.customer_id,

            "recovery_status":
                payment.recovery_status,

            "message":
                "Recovery action cannot be started because this payment is already completed."
        }


    # Get AI-selected recovery action
    action = payment.recovery_action


    # Simulated execution messages
    action_messages = {

        "retry_payment":
            "Recovery agent initiated a payment retry for this customer.",

        "send_payment_link":
            "Recovery agent generated a new payment link for this customer.",

        "request_new_payment_method":
            "Recovery agent requested the customer to provide a new payment method.",

        "manual_review":
            "Recovery agent routed this payment for manual review."
    }


    message = action_messages.get(
        action,
        "Recovery agent initiated the recommended recovery action."
    )


    return {

        "payment_id":
            payment.id,

        "customer_id":
            payment.customer_id,

        "amount":
            payment.amount,

        "recovery_action":
            action,

        "risk_score":
            payment.risk_score,

        "priority":
            payment.priority,

        "recovery_status":
            "recovery_started",

        "message":
            message
    }


# =========================================================
# UPDATE RECOVERY STATUS
# =========================================================

@app.put("/api/payments/{payment_id}/status")
def update_payment_status(
    payment_id: int,
    status: str,
    db: Session = Depends(get_db)
):

    allowed_statuses = {
        "pending",
        "success",
        "failed"
    }


    # -----------------------------------------------------
    # VALIDATE STATUS
    # -----------------------------------------------------

    if status not in allowed_statuses:

        return {

            "error":
                "Invalid status",

            "allowed_statuses":
                list(allowed_statuses)
        }


    # -----------------------------------------------------
    # FIND PAYMENT
    # -----------------------------------------------------

    payment = db.query(Payment).filter(
        Payment.id == payment_id
    ).first()


    # Payment not found
    if payment is None:

        return {
            "error": "Payment not found"
        }


    # -----------------------------------------------------
    # UPDATE STATUS
    # -----------------------------------------------------

    payment.recovery_status = status


    # Save change
    db.commit()
    db.refresh(payment)


    return {

        "payment_id":
            payment.id,

        "customer_id":
            payment.customer_id,

        "recovery_status":
            payment.recovery_status,

        "message":
            "Recovery status updated successfully"
    }