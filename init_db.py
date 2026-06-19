from app.core.database import engine, SessionLocal
from app.models.base import Base
from app.models import User, Customer, Trademark
from app.core.security import hash_password
from app.utils.date_utils import calculate_grace_period_end
from datetime import date, timedelta
import sys


def init_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            print("Creating default admin user...")
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                full_name="系统管理员",
                phone="13800138000",
                role="admin"
            )
            db.add(admin)

        agent = db.query(User).filter(User.username == "agent").first()
        if not agent:
            print("Creating default agent user...")
            agent = User(
                username="agent",
                email="agent@example.com",
                hashed_password=hash_password("agent123"),
                full_name="张代理人",
                phone="13800138001",
                role="agent"
            )
            db.add(agent)

        finance = db.query(User).filter(User.username == "finance").first()
        if not finance:
            print("Creating default finance user...")
            finance = User(
                username="finance",
                email="finance@example.com",
                hashed_password=hash_password("finance123"),
                full_name="李财务",
                phone="13800138002",
                role="finance"
            )
            db.add(finance)

        customer = db.query(Customer).filter(Customer.unified_social_credit_code == "91110000MA001ABC12").first()
        if not customer:
            print("Creating sample customer...")
            customer = Customer(
                name="示例科技有限公司",
                unified_social_credit_code="91110000MA001ABC12",
                legal_representative="王总",
                phone="010-12345678",
                email="contact@example.com",
                address="北京市海淀区中关村大街1号",
                industry="互联网科技",
                remarks="重要客户"
            )
            db.add(customer)
            db.flush()

            sample_expiry = date.today() + timedelta(days=90)
            trademark = db.query(Trademark).filter(Trademark.registration_number == "12345678").first()
            if not trademark:
                print("Creating sample trademark...")
                trademark = Trademark(
                    registration_number="12345678",
                    trademark_name="示例商标",
                    international_class=9,
                    application_date=date(2014, 6, 1),
                    registration_date=date(2015, 6, 1),
                    expiry_date=sample_expiry,
                    grace_period_end=calculate_grace_period_end(sample_expiry),
                    designated_countries="中国",
                    status="materials_pending",
                    current_stage="材料准备",
                    notes="示例商标，用于测试",
                    customer_id=customer.id,
                    assigned_agent_id=agent.id,
                    has_subject_change=0
                )
                db.add(trademark)

                sample_expiry2 = date.today() + timedelta(days=30)
                trademark2 = Trademark(
                    registration_number="87654321",
                    trademark_name="测试商标",
                    international_class=35,
                    application_date=date(2014, 3, 1),
                    registration_date=date(2015, 3, 1),
                    expiry_date=sample_expiry2,
                    grace_period_end=calculate_grace_period_end(sample_expiry2),
                    designated_countries="中国",
                    status="fee_pending",
                    current_stage="费用确认",
                    notes="测试商标，费用待确认",
                    customer_id=customer.id,
                    assigned_agent_id=agent.id,
                    has_subject_change=0
                )
                db.add(trademark2)

        db.commit()
        print("Database initialized successfully!")
        print("\nDefault accounts:")
        print("  - admin / admin123 (管理员)")
        print("  - agent / agent123 (代理人)")
        print("  - finance / finance123 (财务)")
        print("\nSample data created:")
        print("  - Customer: 示例科技有限公司")
        print("  - Trademarks: 2个示例商标")

    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
