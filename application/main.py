"""Entry point."""

from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    """
    Health check API Endpoint
    :return: None
    """
    return {"message": "Service is Healthy"}
