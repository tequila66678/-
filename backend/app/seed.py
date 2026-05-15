"""Seed default data: admin account, sport events with scoring standards, config."""
from .database import SessionLocal
from .models import Admin, SportEvent, ScoringStandard, SystemConfig, Gender, InputFormat
from .auth import hash_password

FEMALE_STANDARDS = {
    "800米跑": ["3'25", "3'35", "3'45", "3'55", "4'05", "4'15", "4'25", "4'35", "4'45", "4'55"],
    "足球运球": ["10.1", "11.0", "11.9", "12.9", "14.4", "15.4", "16.8", "17.7", "18.6", "19.7"],
    "50米跑": ["8.1", "8.3", "8.5", "8.7", "8.9", "9.1", "9.5", "9.9", "10.5", "10.9"],
    "立定跳远": ["1.97", "1.89", "1.81", "1.73", "1.65", "1.57", "1.49", "1.41", "1.33", "1.21"],
    "一分钟跳绳": ["170", "160", "150", "140", "130", "120", "110", "100", "90", "80"],
    "掷实心球": ["6.70", "6.30", "5.90", "5.50", "5.10", "4.70", "4.30", "3.90", "3.50", "3.10"],
    "篮球运球投篮": ["26", "32", "40", "46", "51", "56", "61", "66", "70", "85"],
    "一分钟仰卧起坐": ["50", "46", "42", "38", "34", "30", "26", "22", "18", "14"],
    "游泳": ["100", "90", "80", "70", "60", "50", "40", "30", "25", "1"],
}

MALE_STANDARDS = {
    "1000米跑": ["3'40", "3'50", "4'00", "4'10", "4'20", "4'30", "4'40", "4'50", "5'00", "5'10"],
    "足球运球": ["9.1", "10.0", "10.7", "11.5", "12.8", "13.6", "14.6", "15.2", "15.9", "16.8"],
    "50米跑": ["7.1", "7.3", "7.5", "7.7", "7.9", "8.1", "8.3", "8.7", "9.3", "9.7"],
    "立定跳远": ["2.46", "2.38", "2.30", "2.22", "2.14", "2.06", "1.98", "1.90", "1.82", "1.70"],
    "一分钟跳绳": ["180", "170", "160", "150", "140", "130", "120", "110", "100", "90"],
    "掷实心球": ["9.80", "9.20", "8.60", "8.00", "7.40", "6.80", "6.20", "5.60", "5.00", "4.40"],
    "篮球运球投篮": ["20", "24", "32", "38", "43", "48", "53", "57", "61", "69"],
    "引体向上": ["10", "9", "8", "7", "6", "5", "4", "3", "2", "1"],
    "游泳": ["100", "90", "80", "70", "60", "50", "40", "30", "25", "1"],
}

EVENT_META = {
    "800米跑": {"gender": Gender.F, "higher_better": False, "unit": "分'秒", "input_format": InputFormat.time_ms, "sort_order": 1},
    "1000米跑": {"gender": Gender.M, "higher_better": False, "unit": "分'秒", "input_format": InputFormat.time_ms, "sort_order": 1},
    "足球运球": {"gender": Gender.both, "higher_better": False, "unit": "秒", "input_format": InputFormat.decimal_seconds, "sort_order": 2},
    "50米跑": {"gender": Gender.both, "higher_better": False, "unit": "秒", "input_format": InputFormat.decimal_seconds, "sort_order": 3},
    "立定跳远": {"gender": Gender.both, "higher_better": True, "unit": "米", "input_format": InputFormat.decimal_meters, "sort_order": 4},
    "一分钟跳绳": {"gender": Gender.both, "higher_better": True, "unit": "次", "input_format": InputFormat.integer, "sort_order": 5},
    "掷实心球": {"gender": Gender.both, "higher_better": True, "unit": "米", "input_format": InputFormat.decimal_meters, "sort_order": 6},
    "篮球运球投篮": {"gender": Gender.both, "higher_better": False, "unit": "秒", "input_format": InputFormat.decimal_seconds, "sort_order": 7},
    "一分钟仰卧起坐": {"gender": Gender.F, "higher_better": True, "unit": "次", "input_format": InputFormat.integer, "sort_order": 8},
    "引体向上": {"gender": Gender.M, "higher_better": True, "unit": "个", "input_format": InputFormat.integer, "sort_order": 8},
    "游泳": {"gender": Gender.both, "higher_better": True, "unit": "米", "input_format": InputFormat.integer, "sort_order": 9},
}

def seed():
    db = SessionLocal()

    if db.query(Admin).first():
        print("Already seeded, skipping.")
        db.close()
        return

    # Default admin
    admin = Admin(
        username="admin",
        password_hash=hash_password("admin123"),
        is_super=True,
        display_name="超级管理员"
    )
    db.add(admin)

    # Sport events with standards
    for name, meta in EVENT_META.items():
        event = SportEvent(
            name=name,
            gender=meta["gender"],
            higher_better=meta["higher_better"],
            unit=meta["unit"],
            input_format=meta["input_format"],
            sort_order=meta["sort_order"]
        )
        db.add(event)
        db.flush()

        if name in FEMALE_STANDARDS:
            for i, val in enumerate(FEMALE_STANDARDS[name]):
                db.add(ScoringStandard(event_id=event.id, score=10 - i, standard_value=val))
        if name in MALE_STANDARDS:
            for i, val in enumerate(MALE_STANDARDS[name]):
                db.add(ScoringStandard(event_id=event.id, score=10 - i, standard_value=val))

    # System config
    configs = [
        SystemConfig(key="school_name", value="江东中心学校体育成绩管理中心"),
        SystemConfig(key="praise_threshold", value="1"),
        SystemConfig(key="warning_threshold", value="2"),
        SystemConfig(key="designer", value="tequila"),
    ]
    for c in configs:
        db.add(c)

    db.commit()
    db.close()
    print("Seed data created successfully.")

if __name__ == "__main__":
    seed()
