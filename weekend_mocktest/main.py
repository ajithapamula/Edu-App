# -*- coding: utf-8 -*-
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import config
from .core.database import get_db_manager, close_db_manager
from .core.ai_services import get_ai_service
from .core.utils import cleanup_all
from .api.routes import router

logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Mock Test API - Production starting...")
    try:
        validation = config.validate()
        if not validation["valid"]:
            raise Exception(f"Configuration invalid: {validation['issues']}")

        logger.info("Configuration validated")

        logger.info("Initializing database...")
        db_manager = get_db_manager()
        db_health = db_manager.validate_connection()
        if not db_health["overall"]:
            raise Exception(f"Database validation failed: {db_health}")
        logger.info("Database connected and validated")

        logger.info("Initializing AI service...")
        ai_service = get_ai_service()
        ai_health = ai_service.health_check()
        if ai_health["status"] != "healthy":
            raise Exception(f"AI service validation failed: {ai_health}")
        logger.info("AI service connected and validated")

        logger.info("Testing core functionality...")
        from .services.test_service import get_test_service
        test_service = get_test_service()
        service_health = test_service.health_check()
        if service_health["status"] != "healthy":
            logger.warning("Test service health warning: %s", service_health)

        logger.info("All systems operational")
    except Exception as e:
        logger.error("Startup failed: %s", e)
        raise Exception(f"Application startup failed: {e}")

    yield

    logger.info("Shutting down...")
    try:
        cleanup_all()
        close_db_manager()
        logger.info("Graceful shutdown completed")
    except Exception as e:
        logger.error("Shutdown error: %s", e)

app = FastAPI(
    title=config.API_TITLE,
    description=config.API_DESCRIPTION,
    version=config.API_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

cors_origins = os.getenv(
    'CORS_ORIGINS',
    'http://localhost:5174,http://192.168.48.201:5174,https://192.168.48.201:8090,https://192.168.48.201:5174,https://192.168.48.201:5175'
).split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    logger.warning("Validation error: %s", exc)
    return JSONResponse(status_code=400, content={
        "error": "Validation Error",
        "message": str(exc),
        "type": "validation_error",
    })

@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError):
    logger.warning("File not found: %s", exc)
    return JSONResponse(status_code=404, content={
        "error": "Resource Not Found",
        "message": "The requested resource was not found",
        "type": "not_found_error",
    })

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(status_code=500, content={
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "type": "server_error",
    })

@app.get("/health")
async def health_check():
    try:
        health_status = {
            "status": "healthy",
            "service": "mock_test_api",
            "version": config.API_VERSION,
        }
        try:
            from .services.test_service import get_test_service
            test_service = get_test_service()
            test_health = test_service.health_check()
            health_status["test_service"] = test_health["status"]
            health_status["active_tests"] = test_health.get("active_tests", 0)
        except Exception as e:
            health_status["test_service"] = "error"
            logger.warning("Test service health check failed: %s", e)

        try:
            ai_service = get_ai_service()
            ai_health = ai_service.health_check()
            health_status["ai_service"] = ai_health["status"]
        except Exception as e:
            health_status["ai_service"] = "error"
            logger.warning("AI service health check failed: %s", e)

        try:
            db_manager = get_db_manager()
            db_health = db_manager.validate_connection()
            health_status["database"] = "healthy" if db_health["overall"] else "degraded"
        except Exception as e:
            health_status["database"] = "error"
            logger.warning("Database health check failed: %s", e)

        return health_status
    except Exception as e:
        logger.error("Health check failed: %s", e)
        return JSONResponse(status_code=503, content={
            "status": "unhealthy",
            "service": "mock_test_api",
            "error": str(e),
        })

@app.get("/info")
async def api_info():
    return {
        "name": config.API_TITLE,
        "version": config.API_VERSION,
        "description": config.API_DESCRIPTION,
        "features": {
            "ai_question_generation": True,
            "real_time_evaluation": True,
            "mongodb_integration": True,
            "pdf_export": True,
            "caching": True,
        },
        "configuration": {
            "questions_per_test": config.QUESTIONS_PER_TEST,
            "dev_time_limit": config.DEV_TIME_LIMIT,
            "non_dev_time_limit": config.NON_DEV_TIME_LIMIT,
            "cache_duration_hours": config.QUESTION_CACHE_DURATION_HOURS,
        },
        "endpoints": {
            "start_test": "POST /api/test/start",
            "submit_answer": "POST /api/test/submit",
            "get_results": "GET /api/test/results/{test_id}",
            "download_pdf": "GET /api/test/pdf/{test_id}",
            "health": "GET /health",
            "docs": "GET /docs",
        },
    }
