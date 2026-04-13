"""Health check endpoints for monitoring and Kubernetes probes."""
from fastapi import APIRouter
from datetime import datetime, timezone
import psutil

router = APIRouter(tags=["health"])


@router.get("/health/memory")
async def memory_check():
    mem = psutil.virtual_memory()
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "used_percent": mem.percent,
        },
        "warning": mem.percent > 80,
    }


@router.get("/health/ready")
async def readiness_check():
    try:
        import os
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(os.environ.get("MONGO_URL"), serverSelectionTimeoutMS=3000)
        await client.admin.command("ping")
        return {"status": "ready", "mongodb": "connected"}
    except Exception as e:
        return {"status": "not_ready", "mongodb": "disconnected", "error": str(e)}


@router.get("/health/live")
async def liveness_check():
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}
