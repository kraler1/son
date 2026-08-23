import os
import sys
import subprocess
import time
import urllib.request

# cPanel Python Passenger Entegrasyonu
STREAMLIT_PORT = 8501

def check_streamlit_running():
    try:
        response = urllib.request.urlopen(f"http://127.0.0.1:{STREAMLIT_PORT}/_stcore/health", timeout=2)
        return response.getcode() == 200
    except Exception:
        return False

def application(environ, start_response):
    # Streamlit çalışmıyorsa arka planda başlat
    if not check_streamlit_running():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cmd = [
            sys.executable, "-m", "streamlit", "run",
            os.path.join(current_dir, "app.py"),
            f"--server.port={STREAMLIT_PORT}",
            "--server.address=127.0.0.1",
            "--server.headless=true"
        ]
        subprocess.Popen(cmd, cwd=current_dir)
        time.sleep(3)

    # Basit yönlendirme / karşılama
    status = '200 OK'
    output = f"""
    <html>
        <head>
            <meta http-equiv="refresh" content="2;url=http://{environ.get('HTTP_HOST', 'localhost')}:{STREAMLIT_PORT}" />
            <title>BIST Terminal Yükleniyor...</title>
            <style>
                body {{ background: #0E1117; color: white; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
                .box {{ text-align: center; background: #161B22; padding: 40px; border-radius: 12px; border: 1px solid #30363D; }}
            </style>
        </head>
        <body>
            <div class="box">
                <h2>🚀 BIST & TEFAS Terminali Başlatılıyor...</h2>
                <p>Lütfen birkaç saniye bekleyin, terminale yönlendiriliyorsunuz.</p>
            </div>
        </body>
    </html>
    """.encode('utf-8')

    response_headers = [('Content-type', 'text/html; charset=utf-8'),
                        ('Content-Length', str(len(output)))]
    start_response(status, response_headers)
    return [output]
