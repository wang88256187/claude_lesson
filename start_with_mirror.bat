@echo off
cd backend
set HF_ENDPOINT=https://hf-mirror.com
F:\miniconda\envs\ragchatbot\python.exe -m uvicorn app:app --reload --port 8000
