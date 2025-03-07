import os
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import httpx
from pydantic import BaseModel
from prompt_templates import PET_CARE_INSTRUCTION_PROMPT

app = FastAPI(title="Veterinary Clinic Assistant")

# Set up templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configuration for APIs
WEBUI_ENABLED = True
WEBUI_BASE_URL = "https://chat.ivislabs.in/api"
API_KEY = "sk-d6dd7e8c96c9437e8c5844dfb01ae405"
DEFAULT_MODEL = "gemma2:2b"

OLLAMA_ENABLED = True
OLLAMA_HOST = "localhost"
OLLAMA_PORT = "11434"
OLLAMA_API_URL = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}/api"

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def generate_pet_care_instructions(
    pet_type: str = Form(...),
    issue: Optional[str] = Form(None),  # Made issue optional
    include_follow_up: bool = Form(True),
    tone: str = Form("friendly"),
    num_instructions: int = Form(3),
    model: str = Form(DEFAULT_MODEL)
):
    try:
        # Update the prompt to include the issue if provided
        if issue:
            prompt = PET_CARE_INSTRUCTION_PROMPT.format(
                num_instructions=num_instructions,
                pet_type=pet_type,
                tone=tone,
                issue=issue
            )
        else:
            prompt = PET_CARE_INSTRUCTION_PROMPT.format(
                num_instructions=num_instructions,
                pet_type=pet_type,
                tone=tone,
                issue="general care"  # Default value when issue is not provided
            )

        if WEBUI_ENABLED:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{WEBUI_BASE_URL}/chat/completions",
                        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                        json={"model": model, "messages": [{"role": "user", "content": prompt}]},
                        timeout=60.0
                    )
                    if response.status_code == 200:
                        result = response.json()
                        generated_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                        if generated_text:
                            return {"generated_instructions": generated_text}
            except Exception as e:
                print(f"Open-webui API attempt failed: {str(e)}")

        if OLLAMA_ENABLED:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OLLAMA_API_URL}/generate",
                    json={"model": model, "prompt": prompt, "stream": False},
                    timeout=60.0
                )
                if response.status_code == 200:
                    result = response.json()
                    return {"generated_instructions": result.get("response", "")}

        raise HTTPException(status_code=500, detail="Failed to generate pet care instructions")

    except Exception as e:
        print(f"Error generating pet care instructions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating pet care instructions: {str(e)}")

@app.get("/models")
async def get_models():
    try:
        if WEBUI_ENABLED:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{WEBUI_BASE_URL}/models",
                    headers={"Authorization": f"Bearer {API_KEY}"}
                )
                if response.status_code == 200:
                    models_data = response.json()
                    return {"models": [model["id"] for model in models_data.get("data", [])]}

        if OLLAMA_ENABLED:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{OLLAMA_API_URL}/tags")
                if response.status_code == 200:
                    return {"models": [model.get("name") for model in response.json().get("models", [])]}

        return {"models": [DEFAULT_MODEL]}
    except Exception as e:
        print(f"Unexpected error in get_models: {str(e)}")
        return {"models": [DEFAULT_MODEL]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

