A Telegram group auto-delete + punishment bot (based on Pyrogram).


## Setup


1. Copy `.env.example` to `.env` and fill in your values.
2. Either edit `main.py` to import from `config.py` or replace the placeholder values in `main.py` with your own.

## Environment Variables

Required Variables

- `BOT_TOKEN`: Create a bot using [@BotFather](https://telegram.dog/BotFather), and get the Telegram API token.
- `API_ID`: Get this value from [telegram.org](https://my.telegram.org/apps).
- `API_HASH`: Get this value from [telegram.org](https://my.telegram.org/apps).
- `OWNER_USERNAME`: User ID of owner.
- `ADMIN_ID`: User ID of Admins. 
- `MONGO_URI`: Link to connect postgresql database (setup details given below).  


Recommended (quick):
- Add at top of `main.py` after imports:
```py

from config import *

# And remove/replace the blank assignment lines for API_ID, API_HASH, etc.

# Install dependencies: pip install -r requirements.txt
# Run the bot: python main.py

Docker : Build and run with docker-compose up -d --build after creating .env.
