from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Document Check Service",
        description="AI-agent for document package verification",
        version="1.0.0",
    )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
