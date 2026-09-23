from fastapi import APIRouter
from schemas.payment import PaymentRequest
from agents.recovery_agent import decide_recovery_action

router = APIRouter()


@router.post("/analyze-payment")
def analyze_payment(payment: PaymentRequest):

    recovery = decide_recovery_action(
        payment.failure_reason,
        payment.retry_count
    )

    return {
        "customer_id": payment.customer_id,
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "failure_reason": payment.failure_reason,
        "recovery_action": recovery["action"],
        "customer_message": recovery["message"],
        "retry_count": recovery["retry_count"],
        "risk_score": recovery["risk_score"],
        "priority": recovery["priority"]
    }