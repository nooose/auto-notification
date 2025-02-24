import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

class TelegramListener:

    def __init__(self, token, trader):
        self.token = token
        self.trader = trader

    async def run(self):
        app = Application.builder().token(self.token).build()

        app.add_handler(CommandHandler("stop", self._stop_command))
        app.add_handler(CommandHandler("resume", self._resume_command))

        loop = asyncio.get_event_loop()
        loop.create_task(app.run_polling())

    async def _stop_command(self, update: Update, context: CallbackContext):
        self.trader.stop()
        await update.message.reply_text("거래 중단 완료")

    async def _resume_command(self, update: Update, context: CallbackContext):
        self.trader.resume()
        await update.message.reply_text("거래 재개 완료")
