from sqlmodel import Session, select
from app.core.database import engine, create_db_and_tables
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.plan import Plan
from app.models.product import Product
from app.models.gym import Gym
from decimal import Decimal
from app.core.config import settings

def init_db():
    create_db_and_tables()
    
    with Session(engine) as session:
        # Create default gym if it doesn't exist
        default_gym = session.exec(select(Gym).where(Gym.name == "Line Fitness")).first()
        if not default_gym:
            default_gym = Gym(
                name="Line Fitness",
                address="carrera 74",
                is_active=True
            )
            session.add(default_gym)
            session.commit()
            session.refresh(default_gym)
        
        # Check if admin user already exists
        admin = session.exec(select(User).where(User.email == settings.ADMIN_NAME)).first()
        if not admin:
            # Create default admin user
            admin = User(
                email=settings.ADMIN_NAME,
                full_name="Administrador",
                document_id="Admin",
                phone_number="",
                gym_id=default_gym.id,
                role=UserRole.ADMIN,
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                is_active=True
            )
        else:
            admin.email = settings.ADMIN_NAME
            admin.hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
            
        session.add(admin)
        
        session.commit()
        session.refresh(admin)
        

if __name__ == "__main__":
    init_db() 