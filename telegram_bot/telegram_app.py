# ==========================================================
# ADEL SMART BOT ELITE
# Telegram Application
# ==========================================================

from telegram import (
    Update,
    ReplyKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from interface.bot_interface import BotInterface
from database.database import DatabaseManager


class TelegramApp:
    """
    ==========================================================
    Telegram Interface Layer
    ==========================================================
    """

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(
        self,
        token: str,
        channel_url: str,
        admin_id: int,
        db: DatabaseManager | None = None,
    ):

        self.token = token
        self.channel_url = channel_url
        self.admin_id = admin_id   # يبقى للتوافق مع AdelSmartBot.py

        # إنشاء قاعدة البيانات
        # Runtime composition injects the process journal.  The fallback
        # preserves direct construction in existing tests/tools.
        self.db = db or DatabaseManager()

        # إنشاء تطبيق تيليجرام
        self.application = (
            Application.builder()
            .token(self.token)
            .build()
        )

        # تمرير قاعدة البيانات إلى واجهة البوت
        self.interface = BotInterface(
            channel_url=self.channel_url,
            db=self.db,
            owner_tg_id=self.admin_id,
        )

    @staticmethod
    def _is_greeting(text: str) -> bool:
        return (text or "").strip().casefold() in {"مرحبا", "السلام عليكم", "hi"}

    async def _open_home(self, update: Update, *, include_welcome: bool) -> None:
        """Private-chat home entry point shared by /start and greetings."""
        user = update.effective_user
        if update.message is None or user is None:
            return
        self.db.add_user(user.id, user.first_name, user.username)
        self.db.update_user_activity(user.id)
        page = self.interface.open_main_page(first_name=user.first_name or "Trader", user_id=user.id)
        keyboard = ReplyKeyboardMarkup(page["keyboard"], resize_keyboard=True)
        if include_welcome:
            await update.message.reply_text(
                text=page["welcome_message"],
                disable_web_page_preview=True,
            )
        await update.message.reply_text(
            text=page["home_message"],
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    # ==========================================================
    # START COMMAND
    # ==========================================================

    async def start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        تنفيذ أمر /start
        """

        if update.message is None:
            return

        # منع واجهة /start عن المجموعات والقنوات
        chat = update.effective_chat
        if chat is None or chat.type != "private":
            return

        await self._open_home(update, include_welcome=True)

    # ==========================================================
    # BUTTON HANDLER
    # ==========================================================

    async def handle_button(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        معالجة جميع ضغطات الأزرار.
        """

        if update.message is None:
            return

        # منع الواجهة تمامًا عن المجموعات والقنوات
        chat = update.effective_chat
        if chat is None or chat.type != "private":
            return

        user = update.effective_user

        if user is None:
            return

        if self._is_greeting(update.message.text):
            await self._open_home(update, include_welcome=True)
            return

        self.db.add_user(user.id, user.first_name, user.username)
        self.db.update_user_activity(user.id)

        response = self.interface.handle_button(
            button_text=update.message.text,
            first_name=user.first_name or "Trader",
            user_id=user.id
        )

        keyboard = ReplyKeyboardMarkup(
            response["keyboard"],
            resize_keyboard=True
        )

        await update.message.reply_text(
            text=response["message"],
            reply_markup=keyboard,
            disable_web_page_preview=True,
            parse_mode=response.get("parse_mode"),
        )

    # ==========================================================
    # REGISTER HANDLERS
    # ==========================================================

    def register_handlers(self):
        """
        تسجيل جميع أوامر ومعالجات Telegram.
        """

        self.application.add_handler(
            CommandHandler(
                "start",
                self.start
            )
        )

        # استقبال كل الرسائل النصية (خاص + مجموعات)،
        # لكن handle_button نفسه لن يعمل إلا في الخاص
        self.application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handle_button
            )
        )

    # ==========================================================
    # GET APPLICATION
    # ==========================================================

    def get_application(self) -> Application:
        """
        تجهيز وإرجاع Telegram Application.
        """

        self.register_handlers()
        return self.application
