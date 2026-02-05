import sys
import socket
import asyncio
from threading import Thread
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap
from ui import MainWindow
from server import WebSocketServer
from qr_utils import generate_qr

PORT = 8765

def get_local_ip():
    """Get local LAN IP address"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # ---------- ASYNCIO LOOP IN BACKGROUND THREAD ----------
    loop = asyncio.new_event_loop()
    thread = None
    
    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()
    
    def ensure_loop_running():
        nonlocal thread
        if thread is None or not thread.is_alive():
            thread = Thread(target=run_loop, daemon=True)
            thread.start()
    
    # ---------- SERVER ----------
    server = WebSocketServer(
        port=PORT,
        on_connect=lambda: window.set_connected(True),
        on_disconnect=lambda: window.set_connected(False),
    )
    
    # ---------- START SERVER ----------
    def start_server():
        ensure_loop_running()
        
        # Generate QR code when server starts
        ip = get_local_ip()
        ws_url = f"ws://{ip}:{PORT}/test"
        print("QR URL:", ws_url)
        qr_img = generate_qr(ws_url)
        pixmap = QPixmap.fromImage(qr_img)
        window.set_qr(pixmap)
        
        window.set_server_running(True)
        asyncio.run_coroutine_threadsafe(server.start(), loop)
    
    # ---------- STOP SERVER ----------
    def stop_server():
        future = asyncio.run_coroutine_threadsafe(server.stop(), loop)
        future.result(timeout=3)  # wait for it to actually finish
        
        # Clear QR code when server stops
        window.clear_qr()
        
        window.set_server_running(False)
    
    # ---------- UI HOOKS ----------
    window.start_button.clicked.connect(start_server)
    window.stop_button.clicked.connect(stop_server)
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()