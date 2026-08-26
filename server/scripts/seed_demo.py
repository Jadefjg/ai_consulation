"""写入演示账号、科室、资讯，空库时自动执行，已有管理员则跳过"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.session import SessionLocal
from models.admin import Admin
from models.article import Article, Notice
from models.department import Department
from models.doctor import Doctor
from models.user import User
from core.security import hash_password

DEPARTMENTS = [
    ("内科", "常见内科疾病诊疗", 1),
    ("心血管内科", "高血压、冠心病等心血管疾病", 2),
    ("内分泌科", "糖尿病、甲状腺疾病", 3),
    ("消化内科", "胃炎、溃疡、肝胆消化疾病", 4),
    ("呼吸内科", "肺炎、哮喘、慢阻肺", 5),
    ("神经内科", "头痛、脑卒中、癫痫", 6),
    ("肾内科", "肾炎、肾功能相关疾病", 7),
    ("血液科", "贫血、白血病等", 8),
    ("风湿免疫科", "痛风、类风湿、免疫性疾病", 9),
    ("感染科", "感染性疾病诊疗", 10),
    ("外科", "普外科常见病", 11),
    ("骨科", "骨折、腰椎、关节疾病", 12),
    ("泌尿外科", "结石、前列腺等", 13),
    ("皮肤科", "湿疹、痤疮、皮炎", 14),
    ("耳鼻喉科", "鼻炎、咽炎、中耳炎", 15),
    ("眼科", "结膜炎、白内障、青光眼", 16),
    ("口腔科", "牙周炎、龋齿", 17),
    ("儿科", "儿童常见病", 18),
    ("妇产科", "妇科常见病", 19),
    ("精神科", "焦虑、抑郁等", 20),
]


def seed_demo() -> bool:
    """
    空库写入演示数据
    :return: 是否实际写入了数据
    """
    db = SessionLocal()
    try:
        if db.query(Admin).first():
            print("[seed] 已存在管理员账号，跳过演示数据初始化")
            return False

        for name, desc, order in DEPARTMENTS:
            db.add(Department(name=name, description=desc, sort_order=order, status=1))
        db.flush()

        dept_map = {d.name: d.id for d in db.query(Department).all()}
        db.add(Admin(
            username="admin",
            password=hash_password("123456"),
            nickname="系统管理员",
            status=1,
        ))
        db.add(Doctor(
            username="doctor",
            password=hash_password("123456"),
            real_name="张伟",
            department_id=dept_map.get("内科"),
            title="主任医师",
            specialty="感冒、发热、常见内科疾病",
            introduction="从事内科临床工作多年，擅长常见病诊治与健康指导。",
            phone="13800000001",
            status=1,
        ))
        db.add(Doctor(
            username="doctor2",
            password=hash_password("123456"),
            real_name="李娜",
            department_id=dept_map.get("心血管内科"),
            title="副主任医师",
            specialty="高血压、冠心病",
            introduction="专注心血管疾病预防与慢病管理。",
            phone="13800000002",
            status=1,
        ))
        db.add(User(
            username="user",
            password=hash_password("123456"),
            real_name="王小明",
            gender=1,
            age=28,
            phone="13900000001",
            allergy_history="青霉素过敏",
            status=1,
        ))
        db.add(Notice(
            title="欢迎使用 AI 智能医疗问诊平台",
            content="本平台提供 AI 问诊、症状推理、在线咨询与预约挂号服务。AI 回答仅供参考，不能替代面诊。",
            status=1,
        ))
        db.add(Notice(
            title="门诊预约须知",
            content="请按预约时段提前到院。如需取消，请在就诊日前通过平台修改预约状态或联系管理员。",
            status=1,
        ))
        db.add(Article(
            title="季节性感冒的预防与护理",
            category="常见病",
            summary="介绍感冒的常见症状、居家护理要点以及何时需要及时就医。",
            content="感冒多由病毒引起，常见症状包括发热、头痛、流涕、咽痛和咳嗽。建议多休息、多饮水，症状加重或持续高热应及时就医。",
            status=1,
        ))
        db.add(Article(
            title="高血压患者的日常管理建议",
            category="慢病管理",
            summary="低盐饮食、规律监测血压，并遵医嘱用药。",
            content="高血压需要长期管理。建议低盐饮食、适量运动、戒烟限酒，并按医嘱服用降压药物，不可自行停药。",
            status=1,
        ))
        db.commit()
        print("[seed] 演示数据初始化完成")
        print("[seed] 管理员 admin / 123456")
        print("[seed] 医生 doctor / 123456 ， doctor2 / 123456")
        print("[seed] 患者 user / 123456")
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo()
