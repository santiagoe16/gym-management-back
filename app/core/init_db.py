from sqlmodel import Session, select
from app.core.database import engine, create_db_and_tables
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.plan import Plan
from app.models.user_plan import UserPlan
from app.models.product import Product
from app.models.gym import Gym
from decimal import Decimal

def init_db():
    create_db_and_tables()
    
    with Session(engine) as session:
        # Create default gym if it doesn't exist
        default_gym = session.exec(select(Gym).where(Gym.name == "Main Gym")).first()
        if not default_gym:
            default_gym = Gym(
                name="Main Gym",
                address="123 Main Street, City, State 12345",
                is_active=True
            )
            session.add(default_gym)
            session.commit()
            session.refresh(default_gym)
            print("Default gym created!")
            print(f"Gym: {default_gym.name} (ID: {default_gym.id})")
        else:
            print("Default gym already exists!")
        
        # Check if admin user already exists
        admin = session.exec(select(User).where(User.email == "admin@gym.com")).first()
        if not admin:
            # Create default admin user
            admin_user = User(
                email="admin@gym.com",
                full_name="System Administrator",
                document_id="ADMIN001",
                phone_number="+1234567890",
                gym_id=default_gym.id,
                role=UserRole.ADMIN,
                hashed_password=get_password_hash("admin123"),
                is_active=True
            )
            session.add(admin_user)
            
            # Create default trainer
            trainer_user = User(
                email="trainer@gym.com",
                full_name="Default Trainer",
                document_id="TRAINER001",
                phone_number="+1234567891",
                gym_id=default_gym.id,
                role=UserRole.TRAINER,
                hashed_password=get_password_hash("trainer123"),
                is_active=True
            )
            session.add(trainer_user)
            
            session.commit()
            print("Default admin and trainer users created!")
            print("Admin: admin@gym.com / admin123 (Document ID: ADMIN001)")
            print("Trainer: trainer@gym.com / trainer123 (Document ID: TRAINER001)")
        else:
            print("Admin user already exists!")
        
        # Create default plans
        plans = session.exec(select(Plan)).all()
        if not plans:
            # Create default plans
            basic_plan = Plan(
                name="Basic Plan",
                price=Decimal("29.99"),
                duration_days=30,
                gym_id=default_gym.id,
                is_active=True
            )
            session.add(basic_plan)
            
            premium_plan = Plan(
                name="Premium Plan",
                price=Decimal("79.99"),
                duration_days=90,
                gym_id=default_gym.id,
                is_active=True
            )
            session.add(premium_plan)
            
            annual_plan = Plan(
                name="Annual Plan",
                price=Decimal("299.99"),
                duration_days=365,
                gym_id=default_gym.id,
                is_active=True
            )
            session.add(annual_plan)
            
            session.commit()
            print("Default plans created!")
            print("- Basic Plan: $29.99 (30 days)")
            print("- Premium Plan: $79.99 (90 days)")
            print("- Annual Plan: $299.99 (365 days)")
        else:
            print("Plans already exist!")
        
        # Create default products
        products = session.exec(select(Product)).all()
        if not products:
            # Create default products
            protein_shake = Product(
                name="Protein Shake",
                price=Decimal("15.99"),
                quantity=50,
                gym_id=default_gym.id,
                is_active=True
            )
            session.add(protein_shake)
            
            water_bottle = Product(
                name="Water Bottle",
                price=Decimal("12.99"),
                quantity=30,
                gym_id=default_gym.id,
                is_active=True
            )
            session.add(water_bottle)
            
            gym_towel = Product(
                name="Gym Towel",
                price=Decimal("8.99"),
                quantity=25,
                gym_id=default_gym.id,
                is_active=True
            )
            session.add(gym_towel)
            
            session.commit()
            print("Default products created!")
            print("- Protein Shake: $15.99 (50 in stock)")
            print("- Water Bottle: $12.99 (30 in stock)")
            print("- Gym Towel: $8.99 (25 in stock)")
        else:
            print("Products already exist!")

if __name__ == "__main__":
    init_db() 