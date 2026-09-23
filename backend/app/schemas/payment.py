from pydantic import BaseModel


class PaymentRequest(BaseModel):
    customer_id: str
    amount: float
    payment_method: str
    failure_reason: str
    retry_count: int = 0