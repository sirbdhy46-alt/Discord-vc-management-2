from flask import Flask
from threading import Thread
import logging

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>✿﹒⟡﹒ Bot is alive! ﹒⟡﹒✿</h1><p>Discord bot is running 24/7 ♡</p>"

@app.route('/ping')
def ping():
    return "pong ✿"

def run():
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
