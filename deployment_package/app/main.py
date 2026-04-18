from fastapi import FastAPI
from app.routers.user_routes import router as user_router

app = FastAPI(
    title="Bank User Service",
    version="1.0.0"
)

# Prefijo /users para coincidir con el mapeo de API Gateway
app.include_router(user_router, prefix="/users", tags=["Users"])

@app.get("/")
def root():
    return {"message": "Servicio de Usuarios en ejecución"}
