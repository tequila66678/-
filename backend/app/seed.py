"""Seed default data: admin account, sport events with gender-separated scoring standards, config."""
from .database import SessionLocal
from .models import Admin, School, SportEvent, ScoringStandard, SystemConfig, Gender, InputFormat
from .auth import hash_password

# Female standards (score 10 down to 1)
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

# Male standards (score 10 down to 1)
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

# Event metadata: name -> (gender_applies_to, higher_better, unit, input_format, sort_order)
EVENT_META = {
    "800米跑": (Gender.F, False, "分'秒", InputFormat.time_ms, 1),
    "1000米跑": (Gender.M, False, "分'秒", InputFormat.time_ms, 1),
    "足球运球": (Gender.both, False, "秒", InputFormat.decimal_seconds, 2),
    "50米跑": (Gender.both, False, "秒", InputFormat.decimal_seconds, 3),
    "立定跳远": (Gender.both, True, "米", InputFormat.decimal_meters, 4),
    "一分钟跳绳": (Gender.both, True, "次", InputFormat.integer, 5),
    "掷实心球": (Gender.both, True, "米", InputFormat.decimal_meters, 6),
    "篮球运球投篮": (Gender.both, False, "秒", InputFormat.decimal_seconds, 7),
    "一分钟仰卧起坐": (Gender.F, True, "次", InputFormat.integer, 8),
    "引体向上": (Gender.M, True, "个", InputFormat.integer, 8),
    "游泳": (Gender.both, True, "米", InputFormat.integer, 9),
}

def seed_school(db, school_id: int):
    """Seed events, standards, and config for a specific school."""
    for name, (gender, higher_better, unit, input_fmt, sort_order) in EVENT_META.items():
        event = SportEvent(
            name=name,
            gender=gender,
            higher_better=higher_better,
            unit=unit,
            input_format=input_fmt,
            sort_order=sort_order,
            school_id=school_id
        )
        db.add(event)
        db.flush()

        if gender in (Gender.F, Gender.both) and name in FEMALE_STANDARDS:
            for i, val in enumerate(FEMALE_STANDARDS[name]):
                db.add(ScoringStandard(
                    event_id=event.id, gender=Gender.F,
                    score=10 - i, standard_value=val
                ))

        if gender in (Gender.M, Gender.both) and name in MALE_STANDARDS:
            for i, val in enumerate(MALE_STANDARDS[name]):
                db.add(ScoringStandard(
                    event_id=event.id, gender=Gender.M,
                    score=10 - i, standard_value=val
                ))

    configs = [
        SystemConfig(key="school_name", value="体育成绩管理中心", school_id=school_id),
        SystemConfig(key="praise_threshold", value="1", school_id=school_id),
        SystemConfig(key="warning_threshold", value="2", school_id=school_id),
        SystemConfig(key="designer", value="tequila", school_id=school_id),
    ]
    for c in configs:
        db.add(c)

def seed():
    """First-deploy seed: create default school, super-admin, events, config."""
    db = SessionLocal()

    if db.query(Admin).first():
        print("Already seeded, skipping.")
        db.close()
        return

    school = School(name="江东中心学校")
    db.add(school)
    db.flush()

    seed_school(db, school.id)

    # Default super-admin (school_id=None = platform-level)
    admin = Admin(
        username="admin",
        password_hash=hash_password("admin123"),
        is_super=True,
        role="super",
        display_name="超级管理员",
        school_id=None
    )
    db.add(admin)

    db.commit()
    db.close()
    print("Seed data created successfully.")

if __name__ == "__main__":
    seed()
