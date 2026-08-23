@echo off
chcp 65001 > nul
echo ======================================================
echo    BIST Sinyal ve Analiz Platformu Baslatiliyor...
echo ======================================================
echo.
py -m streamlit run app.py
pause
