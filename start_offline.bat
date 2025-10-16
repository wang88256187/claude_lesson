@echo off
echo ========================================
echo  启动 RAG 聊天机器人 (离线模式)
echo ========================================
cd backend
set HF_ENDPOINT=https://hf-mirror.com
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1
echo.
echo [INFO] 使用离线模式启动...
echo [INFO] 服务地址: http://localhost:8000
echo.
F:\miniconda\envs\ragchatbot\python.exe -m uvicorn app:app --reload --port 8000
pause
