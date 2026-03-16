from app.bot.app import create_app
from app.config.logging import logger

if __name__ == "__main__":
    app = create_app()
    app.run_polling(close_loop=False)
