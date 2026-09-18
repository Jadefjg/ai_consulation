from models.operations import AppointmentWaitlist, Notification
from models.user import User
from services.wechat_notify import send_subscription
from core.config import settings

def notify_next(db, doctor_id, work_date, time_slot):
    candidate = db.query(AppointmentWaitlist).filter_by(doctor_id=doctor_id, work_date=work_date, time_slot=time_slot, status=0).order_by(AppointmentWaitlist.id).first()
    if not candidate:
        return False
    candidate.status = 1
    db.add(Notification(user_id=candidate.user_id, title="预约号源已释放", content="您候补的预约时段已有号源，请尽快进入小程序预约。", type="waitlist"))
    user = db.query(User).filter(User.id == candidate.user_id).first()
    send_subscription(getattr(user, "wx_openid", None), settings.wechat_subscribe_template_id, {"thing1":{"value":"预约号源已释放"}, "date2":{"value":str(work_date)}, "thing3":{"value":time_slot}}, settings.wechat_subscribe_page)
    return True
