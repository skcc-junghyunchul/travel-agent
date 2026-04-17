import stripe
from langchain_core.tools import tool
from config.settings import STRIPE_API_KEY

# NOTE: In production, never collect raw card numbers in a CLI or server-side code
# without PCI DSS SAQ D compliance. Use Stripe.js or Stripe Elements for web,
# or Stripe Terminal for in-person. This implementation is for test/demo purposes only.


def _init_stripe():
    stripe.api_key = STRIPE_API_KEY


@tool
def process_payment(
    amount_usd: float,
    description: str,
    card_number: str,
    exp_month: int,
    exp_year: int,
    cvc: str,
    cardholder_name: str,
) -> str:
    """Process a payment using Stripe. Creates a payment method and charges immediately.
    Use test card 4242424242424242 with any future expiry and any CVC in test mode.

    Args:
        amount_usd: Amount to charge in USD (e.g. 299.99)
        description: Description of what's being paid for
        card_number: 16-digit card number
        exp_month: Card expiry month (1-12)
        exp_year: Card expiry year (e.g. 2027)
        cvc: 3 or 4 digit security code
        cardholder_name: Name as it appears on the card
    """
    try:
        _init_stripe()
        amount_cents = int(amount_usd * 100)

        payment_method = stripe.PaymentMethod.create(
            type="card",
            card={
                "number": card_number.replace(" ", ""),
                "exp_month": exp_month,
                "exp_year": exp_year,
                "cvc": cvc,
            },
            billing_details={"name": cardholder_name},
        )

        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            payment_method=payment_method.id,
            description=description,
            confirm=True,
            automatic_payment_methods={"enabled": True, "allow_redirects": "never"},
        )

        if intent.status == "succeeded":
            return (
                f"✅ Payment successful!\n"
                f"Amount: ${amount_usd:.2f} USD\n"
                f"Description: {description}\n"
                f"Payment ID: {intent.id}\n"
                f"Card: **** **** **** {card_number[-4:]}\n"
                f"Status: {intent.status}"
            )
        else:
            return f"Payment status: {intent.status}. Please check your card details."

    except stripe.error.CardError as e:
        return f"Card declined: {e.user_message}"
    except stripe.error.StripeError as e:
        return f"Payment error: {str(e)}"
    except Exception as e:
        return f"Unexpected payment error: {str(e)}"


@tool
def get_payment_status(payment_intent_id: str) -> str:
    """Check the status of a payment by its Payment Intent ID.

    Args:
        payment_intent_id: The payment ID starting with pi_ returned after processing
    """
    try:
        _init_stripe()
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return (
            f"Payment ID: {intent.id}\n"
            f"Amount: ${intent.amount / 100:.2f} {intent.currency.upper()}\n"
            f"Description: {intent.description}\n"
            f"Status: {intent.status}"
        )
    except stripe.error.StripeError as e:
        return f"Error retrieving payment: {str(e)}"


@tool
def refund_payment(payment_intent_id: str, reason: str = "requested_by_customer") -> str:
    """Refund a payment. Full refund only.

    Args:
        payment_intent_id: The payment ID starting with pi_
        reason: Reason for refund: "duplicate", "fraudulent", or "requested_by_customer"
    """
    try:
        _init_stripe()
        refund = stripe.Refund.create(
            payment_intent=payment_intent_id,
            reason=reason,
        )
        return (
            f"✅ Refund issued!\n"
            f"Refund ID: {refund.id}\n"
            f"Amount: ${refund.amount / 100:.2f} USD\n"
            f"Status: {refund.status}\n"
            f"Note: Refunds typically appear in 5-10 business days."
        )
    except stripe.error.StripeError as e:
        return f"Refund error: {str(e)}"
