from bot_modules.core.app import create_app

if __name__ == "__main__":
    app = create_app()
    app.run_polling(close_loop=False)
