def analyze_payment(
    failure_reason: str,
    retry_count: int,
    amount: float,
    previous_failures: int = 0
):
    """
    Analyze a failed payment and recommend
    the most appropriate recovery action.

    Risk score is calculated first.
    Priority and decision explanation are then
    generated from that same final score.
    """

    failure_reason = failure_reason.lower().strip()


    # =========================================================
    # DEFAULT VALUES
    # =========================================================

    recovery_action = "manual_review"

    customer_message = (
        "We could not complete your payment. "
        "Our system recommends reviewing the payment details."
    )

    risk_score = 70

    explanation_parts = []


    # =========================================================
    # FAILURE REASON ANALYSIS
    # =========================================================

    if "insufficient" in failure_reason:

        recovery_action = "send_payment_link"

        customer_message = (
            "Your payment could not be completed due to insufficient funds. "
            "Please try another payment method."
        )

        risk_score = 40

        explanation_parts.append(
            "The payment failed because of insufficient funds."
        )

        explanation_parts.append(
            "A fresh payment link is recommended so the customer "
            "can complete the payment using another payment method."
        )


    elif "declined" in failure_reason:

        recovery_action = "retry_payment"

        customer_message = (
            "Your payment was declined. Please try the payment again "
            "or use another payment method."
        )

        risk_score = 50

        explanation_parts.append(
            "The payment was declined."
        )

        explanation_parts.append(
            "A retry is recommended because the payment may succeed "
            "on another attempt."
        )


    elif "expired" in failure_reason:

        recovery_action = "request_new_payment_method"

        customer_message = (
            "Your payment method appears to have expired. "
            "Please update your payment method."
        )

        risk_score = 60

        explanation_parts.append(
            "The customer's payment method appears to be expired."
        )

        explanation_parts.append(
            "Updating the payment method is recommended "
            "before attempting another payment."
        )


    elif (
        "network" in failure_reason
        or "timeout" in failure_reason
    ):

        recovery_action = "retry_payment"

        customer_message = (
            "The payment could not be completed because of a temporary "
            "connection issue. Please try again."
        )

        risk_score = 30

        explanation_parts.append(
            "The failure appears to be caused by a temporary "
            "network or timeout issue."
        )

        explanation_parts.append(
            "Retrying the payment is recommended."
        )


    else:

        explanation_parts.append(
            "The payment failure reason could not be confidently classified."
        )

        explanation_parts.append(
            "Manual review is recommended to avoid an unsuitable "
            "automated recovery action."
        )


    # =========================================================
    # RETRY ANALYSIS
    # =========================================================

    if retry_count >= 3:

        risk_score += 20

        explanation_parts.append(
            f"The customer has already attempted the payment "
            f"{retry_count} times, indicating repeated retry attempts."
        )

        explanation_parts.append(
            "Further automated retries should therefore be handled carefully."
        )


    elif retry_count == 2:

        risk_score += 10

        explanation_parts.append(
            "The customer has already made two payment attempts, "
            "which increases the recovery risk."
        )


    elif retry_count == 1:

        explanation_parts.append(
            "The customer has already made one previous retry attempt."
        )


    else:

        explanation_parts.append(
            "There have been no previous retry attempts for this payment."
        )


    # =========================================================
    # AMOUNT ANALYSIS
    # =========================================================

    if amount >= 10000:

        risk_score += 10

        explanation_parts.append(
            "The transaction amount is high, so additional risk "
            "has been added."
        )


    elif amount >= 5000:

        risk_score += 5

        explanation_parts.append(
            "The transaction amount is moderately high, "
            "so a small risk adjustment was applied."
        )


    else:

        explanation_parts.append(
            "The transaction amount is within the normal recovery range."
        )


    # =========================================================
    # CUSTOMER HISTORY ANALYSIS
    # =========================================================

    if previous_failures >= 3:

        risk_score += 20

        explanation_parts.append(
            f"The customer has {previous_failures} previous failed payments, "
            "indicating repeated payment problems."
        )


    elif previous_failures == 2:

        risk_score += 10

        explanation_parts.append(
            "The customer has two previous failed payments, "
            "which increases the risk."
        )


    elif previous_failures == 1:

        risk_score += 5

        explanation_parts.append(
            "The customer has one previous failed payment, "
            "so a small history-based risk adjustment was applied."
        )


    else:

        explanation_parts.append(
            "There are no previous failed payments recorded for this customer."
        )


    # =========================================================
    # LIMIT FINAL RISK SCORE
    # =========================================================

    risk_score = min(
        max(risk_score, 0),
        100
    )


    # =========================================================
    # DETERMINE PRIORITY FROM FINAL RISK SCORE
    # =========================================================

    if risk_score >= 70:

        priority = "high"

    elif risk_score >= 40:

        priority = "medium"

    else:

        priority = "low"


    # =========================================================
    # FINAL AI DECISION EXPLANATION
    # =========================================================

    decision_explanation = " ".join(
        explanation_parts
    )

    decision_explanation += (
        f" Final decision: {recovery_action} "
        f"with a risk score of {risk_score}/100 "
        f"and {priority} priority."
    )


    # =========================================================
    # RETURN AI DECISION
    # =========================================================

    return {
        "recovery_action": recovery_action,
        "customer_message": customer_message,
        "risk_score": risk_score,
        "priority": priority,
        "decision_explanation": decision_explanation
    }