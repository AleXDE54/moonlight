import os
import subprocess
import threading
import psutil
import time
import logging
import queue
import io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from functools import wraps

# Configure logging
class LogCapture(logging.Handler):
    def __init__(self, max_logs=100):
        super().__init__()
        self.log_queue = queue.Queue(maxsize=max_logs)
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    def emit(self, record):
        try:
            msg = self.format(record)
            if self.log_queue.full():
                self.log_queue.get()  # Remove oldest log
            self.log_queue.put(msg)
        except Exception:
            self.handleError(record)

    def get_logs(self):
        logs = []
        while not self.log_queue.empty():
            logs.append(self.log_queue.get())
        return logs

# Setup application logging
log_capture = LogCapture()
logging.basicConfig(level=logging.INFO, handlers=[log_capture])
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# Import bot-related configurations
from config import WEB_PANEL_PASSWORD, BOT_START_COMMAND

# Global variables to track bot process and status
bot_process = None
bot_thread = None
bot_start_time = None
bot_log_capture = None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def capture_bot_logs(process):
    global bot_log_capture
    try:
        # Create a new log capture for this bot instance
        bot_log_capture = LogCapture()
        
        # Capture stdout and stderr
        for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
            bot_log_capture.log_queue.put(f"STDOUT: {line.strip()}")
        
        for line in io.TextIOWrapper(process.stderr, encoding="utf-8"):
            bot_log_capture.log_queue.put(f"STDERR: {line.strip()}")
    except Exception as e:
        logger.error(f"Log capture error: {e}")

def start_bot_process():
    global bot_process, bot_start_time, bot_log_capture
    try:
        # Redirect stdout and stderr to capture logs
        bot_process = subprocess.Popen(
            BOT_START_COMMAND, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Start a thread to capture logs
        log_thread = threading.Thread(target=capture_bot_logs, args=(bot_process,))
        log_thread.daemon = True
        log_thread.start()
        
        bot_start_time = time.time()
        logger.info(f"Bot started with PID {bot_process.pid}")
        return True
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return False

def stop_bot_process():
    global bot_process, bot_start_time, bot_log_capture
    if bot_process:
        try:
            # Try graceful termination first
            parent = psutil.Process(bot_process.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
        except psutil.NoSuchProcess:
            pass
        
        # Force kill if still running
        try:
            bot_process.kill()
        except:
            pass
        
        logger.info("Bot stopped")
        bot_process = None
        bot_start_time = None
        bot_log_capture = None
        return True
    return False

def get_bot_status():
    status_data = {
        'status': "Running" if bot_process is not None else "Stopped",
        'uptime': get_bot_uptime(),
        'last_started': datetime.fromtimestamp(bot_start_time).strftime('%Y-%m-%d %H:%M:%S') if bot_start_time else None,
        'logs': get_bot_logs()
    }
    return status_data

def get_bot_uptime():
    global bot_start_time
    if bot_start_time:
        uptime_seconds = int(time.time() - bot_start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"
    return None

def get_bot_logs():
    # Get logs from the current bot log capture or the global log capture
    if bot_log_capture:
        return list(bot_log_capture.log_queue.queue)
    return log_capture.get_logs()

@socketio.on('connect')
def handle_connect():
    # Send initial bot status when client connects
    emit('bot_status_update', get_bot_status())

@socketio.on('request_status')
def handle_status_request():
    # Send current bot status on request
    emit('bot_status_update', get_bot_status())

@socketio.on('request_logs')
def handle_logs_request():
    # Send current logs on request
    emit('bot_logs_update', {'logs': get_bot_logs()})

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def authenticate():
    password = request.form.get('password')
    if password == WEB_PANEL_PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    return render_template('login.html', error='Invalid password')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/start_bot', methods=['POST'])
@login_required
def start_bot():
    if not bot_process:
        if start_bot_process():
            socketio.emit('bot_status_update', get_bot_status())
            return jsonify({"message": "Bot started successfully"})
        return jsonify({"message": "Failed to start bot"}), 500
    return jsonify({"message": "Bot is already running"})

@app.route('/stop_bot', methods=['POST'])
@login_required
def stop_bot():
    if bot_process:
        if stop_bot_process():
            socketio.emit('bot_status_update', get_bot_status())
            return jsonify({"message": "Bot stopped successfully"})
        return jsonify({"message": "Failed to stop bot"}), 500
    return jsonify({"message": "Bot is not running"})

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
