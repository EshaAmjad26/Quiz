# QUIZ/app.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from quiz8 import generate_quiz

app = FastAPI()

# Allow frontend to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

quiz_data = generate_quiz()

@app.get("/get-quiz")
def get_quiz():
    return {"quiz": [{k: q[k] for k in q if k != "answer"} for q in quiz_data]}

@app.post("/submit-quiz")
async def submit_quiz(request: Request):
    data = await request.json()
    answers = data.get("answers", [])
    score = sum(1 for i, q in enumerate(quiz_data) if i < len(answers) and answers[i] == q["answer"])
    return JSONResponse({"score": score, "total": len(quiz_data)})

# To run: uvicorn app:app --reload
