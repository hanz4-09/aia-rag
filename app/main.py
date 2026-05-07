from fastapi import FastAPI

from app.api.chat import router as chat_router


app = FastAPI(
    title="AIA RAG Case Study Service",
    description="A configurable RAG QA service over internal knowledge base.",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(chat_router)