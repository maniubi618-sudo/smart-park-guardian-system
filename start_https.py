
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main_https import app
import uvicorn

if __name__ == "__main__":
    cert_dir = os.path.join(os.path.dirname(__file__), "app")
    cert_file = os.path.join(cert_dir, "server.crt")
    key_file = os.path.join(cert_dir, "server.key")
    
    print("Starting HTTPS server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8443,
        ssl_certfile=cert_file,
        ssl_keyfile=key_file
    )
