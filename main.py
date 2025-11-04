import os
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from models import PolicyBriefRequest
from llm_service import generate_policy_brief

load_dotenv()

app = FastAPI(title="PolicyLens API")

@app.post("/brief")
async def create_policy_brief(request: PolicyBriefRequest):
    try:
        result = generate_policy_brief(
            document=request.document,
            audience=request.audience,
            language=request.language
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok"}