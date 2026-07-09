from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.checks import router as checks_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Document Check Service",
        description="AI-agent for document package verification",
        version="1.0.0",
    )

    app.include_router(auth_router)
    app.include_router(checks_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
