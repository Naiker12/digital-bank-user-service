from fastapi import FastAPI
from app.routes.user_routes import router as user_router

app = FastAPI(
    title="Bank User Service",
    version="1.0.0"
)

app.include_router(user_router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"message": "User Service Running"}
