# Telegram AI Bot with Web Management Panel

## Overview
A powerful Telegram bot with an advanced web management panel, featuring real-time logging, status tracking, and easy control.

## Features
- 🤖 AI-powered Telegram bot
- 🌐 Web-based management dashboard
- 🔒 Secure password authentication
- 📊 Real-time bot status monitoring
- 📝 Live console log tracking
- 🕒 Precise uptime tracking

## Prerequisites
- Python 3.10+
- pip (Python package manager)

## Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/g4f_telegram_aibot.git
cd g4f_telegram_aibot
```

2. Create a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configuration
- Copy `config.py.example` to `config.py`
- Edit `config.py` with your:
  * Telegram Bot Token
  * Web Panel Password
  * Other settings

## Running the Bot

### Start Telegram Bot
```bash
python bot.py
```

### Start Web Management Panel
```bash
python web.py
```

## Web Panel Access
- Open browser: `http://localhost:5000`
- Login with configured password
- Start/Stop bot
- View real-time logs
- Monitor bot status

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8
```

## Security
- Change default passwords
- Use HTTPS in production
- Keep dependencies updated

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License
[Specify your license here]

## Support
For issues or questions, please open a GitHub issue.
