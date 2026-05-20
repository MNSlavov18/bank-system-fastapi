from fastapi import FastAPI

app = FastAPI(
    title="Bank System API",
    description="Web-based banking system for managing clients, accounts and loans.",
    version="1.0.0"
)


@app.get("/")
def home():
    return {"message": "Bank System API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}