"""
M-Pesa Daraja API Integration
Handles STK Push and C2B payment flows for Safaricom M-Pesa.
Requires environment variables:
  MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, MPESA_SHORTCODE,
  MPESA_PASSKEY, MPESA_CALLBACK_URL, MPESA_ENV (sandbox/production)
"""
import os
import base64
import uuid
from datetime import datetime
import requests as http_requests
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Payment, Lease, User, PaymentStatus, PaymentMethod
from app.schemas.schemas import MpesaSTKPushRequest, MpesaSTKPushResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/mpesa", tags=["mpesa"])

MPESA_ENV = os.environ.get("MPESA_ENV", "sandbox")
MPESA_CONSUMER_KEY = os.environ.get("MPESA_CONSUMER_KEY", "")
MPESA_CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET", "")
MPESA_SHORTCODE = os.environ.get("MPESA_SHORTCODE", "174379")
MPESA_PASSKEY = os.environ.get("MPESA_PASSKEY", "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919")
MPESA_CALLBACK_URL = os.environ.get("MPESA_CALLBACK_URL", "https://example.com/api/mpesa/callback")

BASE_URL = (
    "https://sandbox.safaricom.co.ke" if MPESA_ENV == "sandbox"
    else "https://api.safaricom.co.ke"
)


def get_mpesa_access_token() -> str:
    """Get OAuth access token from Daraja API."""
    if not MPESA_CONSUMER_KEY or not MPESA_CONSUMER_SECRET:
        raise HTTPException(status_code=500, detail="M-Pesa API credentials not configured")

    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    credentials = base64.b64encode(
        f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}".encode()
    ).decode()

    response = http_requests.get(url, headers={"Authorization": f"Basic {credentials}"}, timeout=30)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to get M-Pesa access token")
    return response.json()["access_token"]


def generate_password() -> tuple[str, str]:
    """Generate Lipa Na M-Pesa password and timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    data_to_encode = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(data_to_encode.encode()).decode()
    return password, timestamp


@router.post("/stk-push", response_model=MpesaSTKPushResponse)
async def initiate_stk_push(
    data: MpesaSTKPushRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initiate an STK Push payment to the tenant's phone.
    The tenant will receive a payment prompt on their phone.
    """
    # Verify lease exists
    lease_result = await db.execute(select(Lease).where(Lease.id == data.lease_id))
    lease = lease_result.scalar_one_or_none()
    if not lease:
        raise HTTPException(status_code=404, detail="Lease not found")

    # Format phone number (ensure it starts with 254)
    phone = data.phone_number.strip()
    if phone.startswith("0"):
        phone = "254" + phone[1:]
    elif phone.startswith("+"):
        phone = phone[1:]

    try:
        access_token = get_mpesa_access_token()
        password, timestamp = generate_password()

        account_ref = data.account_reference or f"RENT-{lease.id[:8].upper()}"

        payload = {
            "BusinessShortCode": MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(data.amount),
            "PartyA": phone,
            "PartyB": MPESA_SHORTCODE,
            "PhoneNumber": phone,
            "CallBackURL": MPESA_CALLBACK_URL,
            "AccountReference": account_ref,
            "TransactionDesc": f"Rent payment for {account_ref}"
        }

        url = f"{BASE_URL}/mpesa/stkpush/v1/processrequest"
        response = http_requests.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            timeout=30
        )

        result = response.json()

        if result.get("ResponseCode") == "0":
            # Create a pending payment record
            payment = Payment(
                lease_id=data.lease_id,
                paid_by=current_user.id,
                amount=data.amount,
                payment_method=PaymentMethod.MPESA,
                status=PaymentStatus.PENDING,
                mpesa_phone=phone,
                reference=account_ref,
                transaction_id=result.get("CheckoutRequestID"),
            )
            db.add(payment)
            await db.commit()

            return MpesaSTKPushResponse(
                checkout_request_id=result.get("CheckoutRequestID", ""),
                response_code=result.get("ResponseCode", ""),
                response_description=result.get("ResponseDescription", ""),
                merchant_request_id=result.get("MerchantRequestID", ""),
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("errorMessage", "STK Push failed")
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"M-Pesa STK Push error: {str(e)}")


@router.post("/callback")
async def mpesa_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Callback endpoint for Safaricom to send payment results.
    This is called after the tenant confirms or cancels the STK Push.
    """
    try:
        body = await request.json()
        stk_callback = body.get("Body", {}).get("stkCallback", {})

        checkout_request_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")

        # Find the payment
        result = await db.execute(
            select(Payment).where(Payment.transaction_id == checkout_request_id)
        )
        payment = result.scalar_one_or_none()

        if payment:
            if result_code == 0:
                # Payment successful
                callback_metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
                mpesa_receipt = None
                for item in callback_metadata:
                    if item.get("Name") == "MpesaReceiptNumber":
                        mpesa_receipt = item.get("Value")

                payment.status = PaymentStatus.COMPLETED
                payment.mpesa_receipt = mpesa_receipt
                payment.payment_date = datetime.utcnow()
            else:
                # Payment failed or cancelled
                payment.status = PaymentStatus.FAILED
                payment.notes = stk_callback.get("ResultDesc", "Payment failed")

            await db.commit()

        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    except Exception:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.post("/c2b/confirmation")
async def c2b_confirmation(request: Request, db: AsyncSession = Depends(get_db)):
    """
    C2B Confirmation URL - called when a payment is made to the Paybill/Till.
    Auto-reconciles payment with tenant's rent invoice.
    """
    try:
        body = await request.json()

        trans_id = body.get("TransID")
        amount = float(body.get("TransAmount", 0))
        bill_ref = body.get("BillRefNumber", "")
        phone = body.get("MSISDN", "")
        first_name = body.get("FirstName", "")

        # Try to find a pending payment by reference
        result = await db.execute(
            select(Payment).where(
                Payment.reference == bill_ref,
                Payment.status == PaymentStatus.PENDING
            )
        )
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = PaymentStatus.COMPLETED
            payment.mpesa_receipt = trans_id
            payment.mpesa_phone = phone
            payment.amount = amount
            payment.payment_date = datetime.utcnow()
            await db.commit()
        else:
            # Create a new payment record for unmatched C2B
            # Try to find lease by reference
            lease = None
            if bill_ref:
                lease_result = await db.execute(
                    select(Lease).where(Lease.id.like(f"%{bill_ref}%"))
                )
                lease = lease_result.scalars().first()

            if lease:
                new_payment = Payment(
                    lease_id=lease.id,
                    paid_by=lease.tenant_id,
                    amount=amount,
                    payment_method=PaymentMethod.MPESA,
                    status=PaymentStatus.COMPLETED,
                    mpesa_receipt=trans_id,
                    mpesa_phone=phone,
                    reference=bill_ref,
                    transaction_id=trans_id,
                    payment_date=datetime.utcnow(),
                )
                db.add(new_payment)
                await db.commit()

        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    except Exception:
        return {"ResultCode": 0, "ResultDesc": "Accepted"}


@router.get("/status")
async def mpesa_status():
    """Check M-Pesa integration status."""
    configured = bool(MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET)
    return {
        "configured": configured,
        "environment": MPESA_ENV,
        "shortcode": MPESA_SHORTCODE if configured else None,
        "callback_url": MPESA_CALLBACK_URL if configured else None,
    }
