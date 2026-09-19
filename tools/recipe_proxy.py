#!/usr/bin/env python3
"""Local proxy so src/recipe_agent.html can call Claude without a key in the browser.
  pip install fastapi uvicorn httpx
  ANTHROPIC_API_KEY=sk-ant-... uvicorn tools.recipe_proxy:app --port 8765
Then in recipe_agent.template.html set:  const API = "http://localhost:8765/v1/messages";
"""
import os, httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
@app.post("/v1/messages")
async def messages(req: Request):
    body = await req.json()
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post("https://api.anthropic.com/v1/messages", json=body,
                         headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"})
    return r.json()
