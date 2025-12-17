@echo off
cd /d "%~dp0"

py -m streamlit run "app.py" ^
    --server.address=127.0.0.1 ^
    --server.port=8501 ^
    --browser.serverAddress=127.0.0.1 ^
    --browser.serverPort=8501

pause
