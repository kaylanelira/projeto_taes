import uvicorn
from fastapi import FastAPI

from endpoints.init import api_router

app = FastAPI(
    title="Projeto TAES - SQL Generator",
    version="1.0.0",
    swagger_ui_parameters={"displayRequestDuration": True},
)

app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run("endpoints.server:app", host="0.0.0.0", port=8000, reload=True)
