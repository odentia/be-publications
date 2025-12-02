import uvicorn
import logging
from app import app
from ..core.config import settings

logger = logging.getLogger(__name__)

def main():
    uvicorn.run(
        "posts_service.api.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
        access_log=True,
    )

if __name__ == "__main__":
    main()