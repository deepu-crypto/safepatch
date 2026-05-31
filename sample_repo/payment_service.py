"""
payment_service.py

This file simulates a basic payment service.

Intentional issue:
- Payment amount validation is weak.
"""


def process_payment(user_id, amount, currency):
    """
    Processes a payment.

    Intentional bug:
    The function only checks if amount is None.
    It does not reject zero or negative amounts.
    """

    if amount is None:
        return {
            "status": 400,
            "message": "Amount is required"
        }

    return {
        "status": 200,
        "message": "Payment processed successfully",
        "user_id": user_id,
        "amount": amount,
        "currency": currency
    }
