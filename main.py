# agents/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from .orchestrator import Orchestrator

app = FastAPI(title="orchestrator")
orc = Orchestrator()
class ProcessRequest(BaseModel):
    user_id: str
    message: str
@app.get("/")
def root():
    return {"status": "orchestrator alive"}

@app.post("/process")
def process(req: ProcessRequest):
    res = orc.process(req.user_id, req.message)
    return res

@app.get("/history/{user_id}")
def history(user_id: str, limit: int = 10):
    return {"history": orc.memory.get_history(user_id, limit)}
