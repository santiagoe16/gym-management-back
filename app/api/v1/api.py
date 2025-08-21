from fastapi import APIRouter
from app.api.v1.endpoints import attendances, auth, users, plans, products, sales, gyms, measurements, user_plans

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(gyms.router, prefix="/gyms", tags=["gyms"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(user_plans.router, prefix="/user-plans", tags=["user-plans"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(measurements.router, prefix="/measurements", tags=["measurements"])
api_router.include_router(attendances.router, prefix="/attendance", tags=["attendance"]) 