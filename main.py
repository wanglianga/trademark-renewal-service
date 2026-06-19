from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine
from app.routers import (
    auth,
    customers,
    trademarks,
    materials,
    fees,
    submissions,
    acceptances,
    corrections,
    rejections,
    certificates,
    agencies,
    reminders,
    business,
    progress
)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="商标续展代理进度服务",
    description="商标续展代理业务管理系统 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(customers.router)
app.include_router(trademarks.router)
app.include_router(materials.router)
app.include_router(fees.router)
app.include_router(submissions.router)
app.include_router(acceptances.router)
app.include_router(corrections.router)
app.include_router(rejections.router)
app.include_router(certificates.router)
app.include_router(agencies.router)
app.include_router(reminders.router)
app.include_router(business.router)
app.include_router(progress.router)


@app.get("/health", summary="健康检查")
async def health_check():
    return {"status": "healthy", "message": "商标续展服务运行正常"}


@app.get("/", summary="根路径")
async def root():
    return {
        "name": "商标续展代理进度服务",
        "version": "1.0.0",
        "docs": "/docs",
        "api_prefix": "/api"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_ENV == "development"
    )
