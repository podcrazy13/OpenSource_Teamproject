import os
from openai import OpenAI
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

api_key    = os.getenv("OPENAI_API_KEY")
endpoint   = os.getenv("ENDPOINT_URL")    
deployment = os.getenv("DEPLOYMENT_NAME")    
api_version = "2025-01-01-preview"

client = OpenAI(
    api_key=api_key,
    base_url=f"{endpoint}openai/deployments/{deployment}",
    default_query={"api-version": api_version}
)

app = FastAPI(debug=True)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    temperature: float = 1.0

SYSTEM_MSG = f"""You are a programming professor, Your name is Miran, 36 years old

Current User: 
    - Lectures in Python, AI, and Deep Learning classes
    - Likes machine learning research, golf, and music
    - Enjoys mentoring students and reading science fiction

Communication Style:
    - Explains concepts step-by-step with clarity
    - Maintains a patient, supportive, and constructive tone
"""

def classify_intent(msg: str) -> str:
    prompt = f"""Your job is to classify intent. 

Choose one of the following intents:
- professor_lecture
- Major_support
- Scholarship_support

User: {msg}
Intent:
"""
    try:
        r = client.chat.completions.create(
            model=deployment,              
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        intent = (r.choices[0].message.content or "").strip()
        if intent not in {"professor_lecture","Major_support","Scholarship_support"}:
            intent = "professor_lecture"
        return intent
    except Exception as e:
        return "professor_lecture"

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        intent = classify_intent(req.message)

        if intent == "professor_lecture":
            r = client.chat.completions.create(
                model=deployment,          
                messages=[
                    {"role": "system", "content": SYSTEM_MSG},
                    {"role": "user", "content": req.message},
                ],
                temperature=req.temperature,
            )
            return {"message": r.choices[0].message.content}

        elif intent == "Major_support":
            return {"message": "Here is Department Support number: 1234567890"}

        elif intent == "Scholarship_support":
            return {"message": "Here is Scholarship Support number: 0987654321"}

        return {"message": f"[fallback] intent={intent}"}

    except Exception as e:
        return {"message": f"[server-error] {type(e).__name__}: {e}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
