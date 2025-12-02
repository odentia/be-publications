from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from .lifespan import lifespan
from .v1.post_router import router
from ..core.config import settings
from ..core.logging import init_logging

init_logging()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Posts Service",
        description="Microservice for managing blog posts",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router, prefix=settings.API_V1_PREFIX)

    @app.get("/")
    async def root():
        return {"message": "Posts Service API", "version": "1.0.0"}

    logger.info("Posts Service application created successfully")
    return app


app = create_app()