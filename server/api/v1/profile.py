"""个人中心接口"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from core.deps import get_current_user, CurrentUser
from core.response import success
from core.security import verify_password, hash_password
from db.session import get_db
from schemas.common import ProfileUpdateRequest, PasswordChangeRequest
from utils.helpers import save_upload_file, format_datetime
from utils.file_security import UploadSecurityError, validate_avatar

router = APIRouter()

_AVATAR_MAX_BYTES = 2 * 1024 * 1024


@router.get("/info")
def get_profile(current: CurrentUser = Depends(get_current_user)):
    """获取个人信息"""
    obj = current.obj
    data = {
        "user_id": current.user_id,
        "username": current.username,
        "role": current.role,
        "avatar": getattr(obj, "avatar", None),
        "phone": getattr(obj, "phone", None),
        "create_time": format_datetime(getattr(obj, "create_time", None)),
    }
    if current.role in ("admin", "root"):
        data["nickname"] = obj.nickname
        data["email"] = obj.email
    elif current.role == "doctor":
        data["real_name"] = obj.real_name
        data["title"] = obj.title
        data["specialty"] = obj.specialty
        data["introduction"] = obj.introduction
        data["department_id"] = obj.department_id
    elif current.role == "user":
        data["real_name"] = obj.real_name
        data["gender"] = obj.gender
        data["age"] = obj.age
        data["allergy_history"] = obj.allergy_history
    return success(data)


@router.put("/update")
def update_profile(req: ProfileUpdateRequest, db: Session = Depends(get_db), current: CurrentUser = Depends(get_current_user)):
    """更新个人资料"""
    obj = current.obj
    if current.role in ("admin", "root"):
        if req.nickname is not None: obj.nickname = req.nickname
        if req.phone is not None: obj.phone = req.phone
        if req.email is not None: obj.email = req.email
    elif current.role == "doctor":
        if req.real_name is not None: obj.real_name = req.real_name
        if req.phone is not None: obj.phone = req.phone
        if req.title is not None: obj.title = req.title
        if req.specialty is not None: obj.specialty = req.specialty
        if req.introduction is not None: obj.introduction = req.introduction
    elif current.role == "user":
        if req.real_name is not None: obj.real_name = req.real_name
        if req.phone is not None: obj.phone = req.phone
        if req.gender is not None: obj.gender = req.gender
        if req.age is not None: obj.age = req.age
        if req.allergy_history is not None: obj.allergy_history = req.allergy_history
    db.commit()
    return success(None, "资料更新成功")


@router.put("/password")
def change_password(req: PasswordChangeRequest, db: Session = Depends(get_db), current: CurrentUser = Depends(get_current_user)):
    """修改密码"""
    obj = current.obj
    if not verify_password(req.old_password, obj.password):
        raise HTTPException(status_code=400, detail="原密码错误")
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6个字符")
    if req.old_password == req.new_password:
        raise HTTPException(status_code=400, detail="新密码不能与原密码相同")
    obj.password = hash_password(req.new_password)
    db.commit()
    return success(None, "密码修改成功")


@router.post("/avatar")
async def upload_avatar(file: UploadFile = File(...), db: Session = Depends(get_db), current: CurrentUser = Depends(get_current_user)):
    """上传头像"""
    filename = file.filename or ""
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(content) > _AVATAR_MAX_BYTES:
        raise HTTPException(status_code=400, detail="头像大小不能超过2MB")
    try:
        validate_avatar(filename, content)
    except UploadSecurityError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    rel_path = save_upload_file(content, filename, "avatar")
    current.obj.avatar = rel_path
    db.commit()
    return success({"avatar": rel_path}, "头像上传成功")
