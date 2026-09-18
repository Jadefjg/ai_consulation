import secrets
import hmac, hashlib
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.deps import require_roles, CurrentUser
from core.response import success
from db.session import get_db
from models.operations import PaymentOrder
from core.config import settings
router = APIRouter()
@router.post("/orders")
def create_order(amount: int, business_type: str = "consult", business_id: int | None = None, db: Session = Depends(get_db), current: CurrentUser = Depends(require_roles("user"))):
    if amount <= 0 or amount > 10_000_000: raise HTTPException(status_code=400, detail="金额无效")
    order = PaymentOrder(order_no=f"AI{datetime.now():%Y%m%d%H%M%S}{secrets.token_hex(4)}", user_id=current.user_id, amount=amount, business_type=business_type, business_id=business_id)
    db.add(order); db.commit(); db.refresh(order)
    return success({"id": order.id, "order_no": order.order_no, "amount": order.amount, "status": order.status})
@router.post("/orders/{order_no}/callback")
def payment_callback(order_no: str, transaction_id: str, signature: str = "", db: Session = Depends(get_db)):
    if not settings.payment_callback_secret:
        raise HTTPException(status_code=503, detail="支付回调未配置签名密钥")
    expected = hmac.new(settings.payment_callback_secret.encode(), f"{order_no}:{transaction_id}".encode(), hashlib.sha256).hexdigest()
    if not signature or not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="支付回调签名无效")
    order = db.query(PaymentOrder).filter_by(order_no=order_no).first()
    if not order: raise HTTPException(status_code=404, detail="订单不存在")
    if order.status == "paid": return success(None, "已处理")
    order.status="paid"; order.transaction_id=transaction_id; order.paid_time=datetime.now(); db.commit(); return success(None, "支付成功")
