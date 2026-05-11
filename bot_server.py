"""
bot_server.py — listens for Telegram messages and responds with the plain weather report.
Send any message to your bot to trigger a weather report.
Requires BOT_TOKEN + PORT (set automatically by Railway).
"""

import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from weather_agent import get_weather, format_weather_report, send_telegram

PORT = int(os.environ.get("PORT", 8080))


def handle_update(update: dict) -> None:
    """Process a single Telegram update."""
    try:
        chat_id = update["message"]["chat"]["id"]
    except KeyError:
        return  # not a message we care about, ignore

    # any message triggers a plain report
    try:
        weather_data = get_weather()
        message = format_weather_report(weather_data)
    except Exception as e:
        message = f"something broke: {e}"

    try:
        send_telegram(message, chat_id=chat_id)
    except Exception as e:
        print(f"Failed to reply: {e}")


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            update = json.loads(body)
        except json.JSONDecodeError:
            self.send_response(400)
            self.end_headers()
            return

        # respond to Telegram immediately, process in background
        self.send_response(200)
        self.end_headers()
        threading.Thread(target=handle_update, args=(update,), daemon=True).start()

    def do_GET(self):
        # health check endpoint — Railway uses this to confirm the service is up
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    print(f"Listening on port {PORT}")
    server.serve_forever()
