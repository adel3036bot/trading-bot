# ==========================================================
# ADEL SMART BOT ELITE
# Bot Interface — FINAL LOCKED VERSION
# ==========================================================

from interface.interface_formatter import InterfaceFormatter


class BotInterface:
    """
    مسؤوليات هذا الملف:

    - إدارة جميع قوائم البوت.
    - إدارة الصفحة الرئيسية.
    - إدارة التنقل بين القوائم.
    - إدارة لوحة الإدارة.
    - إدارة واجهة الاشتراكات فقط (بدون منطق دفع).
    - اختيار البطاقة الذكية بعد الترحيب.

    هذا الملف لا يقوم بتحليل السوق،
    ولا يجلب الأخبار،
    ولا ينشئ الصور،
    وإنما يدير واجهة المستخدم فقط.

    الإصدار LOCKED ولا يُفتح لاحقًا إلا عند إضافة ميزة جديدة.
    """

    # ==========================================================
    # MENU NAME CONSTANTS
    # ==========================================================

    MENU_MAIN = "main"
    MENU_MARKET = "market"
    MENU_OPPORTUNITIES = "opportunities"
    MENU_NEWS = "news"
    MENU_REPORTS = "reports"
    MENU_ANALYSIS = "analysis"
    MENU_SETTINGS = "settings"
    MENU_HELP = "help"
    MENU_ADMIN = "admin"
    MENU_CHANNEL = "channel"
    MENU_ADMIN_SUBSCRIPTIONS = "admin_subscriptions"
    MENU_SUBSCRIPTION_PAGE = "subscription_page"

    # ==========================================================
    # BUTTON LABEL CONSTANTS
    # ==========================================================

    BTN_HOME = "🏠 الرئيسية"
    BTN_BACK = "⬅️ رجوع"

    BTN_MARKET = "📈 السوق"
    BTN_OPPORTUNITIES = "🎯 الفرص"
    BTN_NEWS = "📰 الأخبار"
    BTN_REPORTS = "📊 التقارير"
    BTN_ANALYSIS = "🖼 التحليلات"
    BTN_CHANNEL = "📢 القناة الرسمية"
    BTN_SETTINGS = "⚙️ الإعدادات"
    BTN_HELP = "❓ المساعدة"
    BTN_ADMIN_PANEL = "👑 لوحة الإدارة"
    BTN_SUBSCRIPTIONS = "💳 الاشتراك"

    BTN_ADMIN_USERS_LIST = "📋 عرض المستخدمين"
    BTN_ADMIN_SEARCH_USER = "🔍 البحث عن مستخدم"

    BTN_ADMIN_SUBSCRIPTIONS = "💳 إدارة الاشتراكات"
    BTN_ADMIN_SUBSCRIBERS = "👥 المشتركون"
    BTN_ADMIN_EXPIRED = "⏳ الاشتراكات المنتهية"
    BTN_ADMIN_LOGS = "📄 سجل العمليات"
    BTN_ADMIN_FREE_TRIAL = "🎁 التجربة المجانية"
    BTN_ADMIN_SUBS_SETTINGS = "⚙️ إعدادات الاشتراكات"
    BTN_ADMIN_REQUESTS = "🆕 طلبات الاشتراك"

    BTN_SUBS_RENEW = "🔄 تجديد الاشتراك"
    BTN_SUBS_RESEND_INVITE = "🔗 إعادة إرسال رابط الدعوة"
    BTN_SUBS_GO_TO_STORE = "🛒 الذهاب إلى متجر سلة"
    BTN_SUBS_REQUEST_BIWEEKLY = "🗓️ طلب اشتراك أسبوعين"
    BTN_SUBS_REQUEST_MONTHLY = "🗓️ طلب اشتراك شهري"
    BTN_ADMIN_APPROVE_REQUEST_PREFIX = "✅ قبول الطلب رقم "
    BTN_ADMIN_REJECT_REQUEST_PREFIX = "❌ رفض الطلب رقم "

    BTN_INDICES = "📊 المؤشرات"
    BTN_GOLD = "🥇 الذهب"
    BTN_BITCOIN = "₿ البيتكوين"
    BTN_CALENDAR = "📅 التقويم الاقتصادي"
    BTN_COMPLETED_TRADES = "🏆 الصفقات المكتملة"
    BTN_NEWS_PREMARKET = "🌅 ما قبل الافتتاح"
    BTN_NEWS_BREAKING = "🚨 الأخبار العاجلة"
    BTN_NEWS_AFTER_MARKET = "🌙 بعد الإغلاق"
    BTN_DAILY_REPORT = "📅 التقرير اليومي"
    BTN_WEEKLY_REPORT = "📈 التقرير الأسبوعي"
    BTN_MONTHLY_REPORT = "📊 التقرير الشهري"
    BTN_SPX = "📈 SPX"
    BTN_SPY = "📊 SPY"
    BTN_NASDAQ = "💻 NASDAQ"
    BTN_QQQ = "📉 QQQ"
    BTN_LANGUAGE = "🌐 اللغة"
    BTN_NOTIFICATIONS = "🔔 الإشعارات"
    BTN_GUIDE = "📖 دليل الاستخدام"
    BTN_FAQ = "❓ الأسئلة الشائعة"
    BTN_ABOUT = "ℹ️ حول البوت"

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self, channel_url: str, db, owner_tg_id: int | None = None):
        self.channel_url = channel_url
        self.db = db
        self.owner_tg_id = owner_tg_id

        self.formatter = InterfaceFormatter(channel_url=self.channel_url)

        self.user_navigation = {}

    # ==========================================================
    # USER NAVIGATION
    # ==========================================================

    def set_user_menu(self, user_id: int, menu_name: str):
        self.user_navigation.setdefault(user_id, {})
        self.user_navigation[user_id]["current_menu"] = menu_name

    def get_user_menu(self, user_id: int) -> str:
        return self.user_navigation.get(user_id, {}).get("current_menu", self.MENU_MAIN)

    def set_user_state(self, user_id: int, state: str | None):
        self.user_navigation.setdefault(user_id, {})
        self.user_navigation[user_id]["state"] = state

    def get_user_state(self, user_id: int) -> str | None:
        return self.user_navigation.get(user_id, {}).get("state")

    # ==========================================================
    # ROLE SYSTEM (Owner / Admin / User)
    # ==========================================================

    def get_user_role(self, user_id: int) -> str:
        """
        يعيد: "owner" / "admin" / "user"
        يعتمد حصريًا على DatabaseManager.
        """
        return self.db.get_user_role(user_id, owner_tg_id=self.owner_tg_id)

    def is_admin(self, user_id: int) -> bool:
        return self.get_user_role(user_id) in ("owner", "admin")

    def is_owner(self, user_id: int) -> bool:
        return self.get_user_role(user_id) == "owner"

    def _is_admin_action(self, button_text: str) -> bool:
        return button_text.startswith((
            "المستخدم رقم",
            self.BTN_ADMIN_APPROVE_REQUEST_PREFIX,
            self.BTN_ADMIN_REJECT_REQUEST_PREFIX,
        )) or button_text in {
            self.BTN_ADMIN_PANEL,
            self.BTN_ADMIN_USERS_LIST,
            self.BTN_ADMIN_SEARCH_USER,
            self.BTN_ADMIN_SUBSCRIPTIONS,
            self.BTN_ADMIN_SUBSCRIBERS,
            self.BTN_ADMIN_EXPIRED,
            self.BTN_ADMIN_LOGS,
            self.BTN_ADMIN_FREE_TRIAL,
            self.BTN_ADMIN_SUBS_SETTINGS,
            self.BTN_ADMIN_REQUESTS,
        }

    def _subscriber_access_state(self, user_id: int) -> str | None:
        subscription = self.db.get_user_subscription_by_tg_id(user_id)
        if subscription.get("status") == "active":
            return None
        return "EXPIRED_SUBSCRIPTION" if subscription.get("status") == "expired" else "SUBSCRIPTION_REQUIRED"

    # ==========================================================
    # MENUS — النسخة النهائية الصحيحة
    # ==========================================================

    MAIN_MENU = [
        [BTN_MARKET, BTN_OPPORTUNITIES],
        [BTN_NEWS, BTN_REPORTS],
        [BTN_ANALYSIS, BTN_CHANNEL],
        [BTN_SETTINGS, BTN_HELP],
        [BTN_SUBSCRIPTIONS]
    ]

    # ⭐ لوحة الإدارة الرئيسية
    ADMIN_MAIN_MENU = [
        [BTN_ADMIN_USERS_LIST],
        [BTN_ADMIN_SUBSCRIPTIONS],
        [BTN_ADMIN_LOGS],
        [BTN_ADMIN_FREE_TRIAL],
        [BTN_ADMIN_SUBS_SETTINGS],
        [BTN_BACK, BTN_HOME]
    ]

    MARKET_MENU = [
        [BTN_INDICES],
        [BTN_GOLD, BTN_BITCOIN],
        [BTN_CALENDAR],
        [BTN_HOME]
    ]

    OPPORTUNITIES_MENU = [
        [BTN_COMPLETED_TRADES],
        [BTN_HOME]
    ]

    NEWS_MENU = [
        [BTN_NEWS_PREMARKET],
        [BTN_NEWS_BREAKING],
        [BTN_NEWS_AFTER_MARKET],
        [BTN_HOME]
    ]

    REPORTS_MENU = [
        [BTN_DAILY_REPORT],
        [BTN_WEEKLY_REPORT],
        [BTN_MONTHLY_REPORT],
        [BTN_HOME]
    ]

    ANALYSIS_MENU = [
        [BTN_SPX, BTN_SPY],
        [BTN_NASDAQ, BTN_QQQ],
        [BTN_HOME]
    ]

    SETTINGS_MENU = [
        [BTN_LANGUAGE],
        [BTN_NOTIFICATIONS],
        [BTN_HOME]
    ]

    HELP_MENU = [
        [BTN_GUIDE],
        [BTN_FAQ],
        [BTN_ABOUT],
        [BTN_HOME]
    ]

    # ⭐ لوحة الاشتراكات داخل لوحة الإدارة
    ADMIN_MENU = [
        [BTN_ADMIN_USERS_LIST],
        [BTN_ADMIN_SEARCH_USER],
        [BTN_ADMIN_SUBSCRIPTIONS],
        [BTN_BACK, BTN_HOME]
    ]

    CHANNEL_MENU = [
        [BTN_HOME]
    ]


    # ==========================================================
    # HOME PAGE
    # ==========================================================

    def get_main_menu(self, user_id: int):
        """
        الصفحة الرئيسية للمستخدم:
        - المستخدم العادي يرى MAIN_MENU فقط.
        - الأدمن والمالك يحصلون على زر إضافي (👑 لوحة الإدارة) في أعلى القائمة.
        """
        # نأخذ نسخة من القائمة الأساسية حتى لا نعدل الأصل
        menu = [row[:] for row in self.MAIN_MENU]

        # إذا كان المستخدم Admin أو Owner → نضيف زر لوحة الإدارة
        if self.is_admin(user_id):
            menu.insert(0, [self.BTN_ADMIN_PANEL])

        return menu

    def build_home_page(self, first_name: str) -> dict:
        return {
            "welcome_message": self.formatter.build_welcome_message(first_name),
            "smart_card": None,
            "home_message": self.formatter.build_home_message()
        }

    def build_smart_card(self, card_type: str | None):
        if card_type is None:
            return None

        cards = {
            "breaking_news": self.formatter.build_breaking_news_card(),
            "pre_market": self.formatter.build_pre_market_card(),
            "market": self.formatter.build_market_card(),
            "after_market": self.formatter.build_after_market_card()
        }

        return cards.get(card_type)

    def update_home_page(self, first_name: str, card_type: str | None):
        page = self.build_home_page(first_name)
        page["smart_card"] = self.build_smart_card(card_type)
        return page

    def open_main_page(self, first_name: str, user_id: int, card_type: str | None = None):
        """
        فتح الصفحة الرئيسية:
        - يتم تحديد القائمة حسب صلاحية المستخدم.
        - يتم عرض البطاقة الذكية إن وجدت.
        """
        self.set_user_menu(user_id, self.MENU_MAIN)
        page = self.update_home_page(first_name, card_type)
        page["keyboard"] = self.get_main_menu(user_id)
        page["message"] = page["home_message"]
        return page

    def go_home(self, first_name: str, user_id: int):
        return self.open_main_page(first_name, user_id)

    # ==========================================================
    # MENU NAVIGATION
    # ==========================================================

    def get_menu(self, menu_name: str, user_id: int = 0):
        menus = {
            self.MENU_MAIN: self.get_main_menu(user_id),
            self.MENU_MARKET: self.MARKET_MENU,
            self.MENU_OPPORTUNITIES: self.OPPORTUNITIES_MENU,
            self.MENU_NEWS: self.NEWS_MENU,
            self.MENU_REPORTS: self.REPORTS_MENU,
            self.MENU_ANALYSIS: self.ANALYSIS_MENU,
            self.MENU_SETTINGS: self.SETTINGS_MENU,
            self.MENU_HELP: self.HELP_MENU,
            self.MENU_ADMIN: self.ADMIN_MENU,
            self.MENU_CHANNEL: self.CHANNEL_MENU,
            self.MENU_ADMIN_SUBSCRIPTIONS: self.get_admin_subscriptions_keyboard(),
        }
        return menus.get(menu_name)

    def get_keyboard_layout(self, menu_name: str, user_id: int = 0):
        return self.get_menu(menu_name, user_id)

    def get_menu_message(self, menu_name: str) -> str:
        messages = {
            self.MENU_MAIN: self.formatter.build_home_message(),
            self.MENU_MARKET: self.formatter.build_market_message(),
            self.MENU_OPPORTUNITIES: self.formatter.build_opportunities_message(),
            self.MENU_NEWS: self.formatter.build_news_message(),
            self.MENU_REPORTS: self.formatter.build_reports_message(),
            self.MENU_ANALYSIS: self.formatter.build_analysis_message(),
            self.MENU_SETTINGS: self.formatter.build_settings_message(),
            self.MENU_HELP: self.formatter.build_help_message(),
            self.MENU_CHANNEL: self.formatter.build_channel_message(),
            self.MENU_ADMIN: "👑 لوحة الإدارة\n\nاختر من الأزرار بالأسفل.",
            self.MENU_ADMIN_SUBSCRIPTIONS: self.formatter.build_admin_subscriptions_menu_message(),
        }
        return messages.get(menu_name, "🏠 الصفحة الرئيسية")

    def open_menu(self, menu_name: str, user_id: int = 0):
        self.set_user_menu(user_id, menu_name)
        page = {
            "message": self.get_menu_message(menu_name),
            "keyboard": self.get_keyboard_layout(menu_name, user_id)
        }
        if menu_name == self.MENU_CHANNEL:
            page["parse_mode"] = "HTML"
        return page

    # ==========================================================
    # SUBSCRIPTIONS — SMART PAGE
    # ==========================================================

    def get_subscription_mode(self) -> str:
        return self.db.get_subscription_mode()

    def set_subscription_mode(self, mode: str):
        self.db.set_subscription_mode(mode)

    def get_user_subscription(self, user_id: int):
        return self.db.get_user_subscription_by_tg_id(user_id)

    def build_subscription_page(self, user_id: int):
        subscription = self.get_user_subscription(user_id)

        if subscription is None or subscription.get("status") == "none":
            message = self.formatter.build_subscription_plans_message()
            keyboard = [
                [self.BTN_SUBS_REQUEST_BIWEEKLY],
                [self.BTN_SUBS_REQUEST_MONTHLY],
                [self.BTN_BACK],
                [self.BTN_HOME]
            ]
            return {"message": message, "keyboard": keyboard}

        status = subscription.get("status")

        if status == "active":
            message = self.formatter.build_subscription_status_message(subscription)
            keyboard = [
                [self.BTN_SUBS_RENEW, self.BTN_SUBS_RESEND_INVITE],
                [self.BTN_BACK],
                [self.BTN_HOME]
            ]
            return {"message": message, "keyboard": keyboard}

        message = self.formatter.build_subscription_expired_message(subscription)
        keyboard = [
            [self.BTN_SUBS_REQUEST_BIWEEKLY],
            [self.BTN_SUBS_REQUEST_MONTHLY],
            [self.BTN_BACK],
            [self.BTN_HOME]
        ]
        return {"message": message, "keyboard": keyboard}

    # ==========================================================
    # ADMIN — DATABASE WRAPPERS
    # ==========================================================

    def admin_get_users_list(self):
        return self.db.get_users_list()

    def admin_get_user_details(self, user_id: int):
        return self.db.get_user_details(user_id)

    def admin_search_user(self, query: str):
        row = self.db.find_user(query)
        if row is None:
            return None

        return {
            "user_id": row[0],
            "first_name": row[1],
            "username": row[2],
            "subscription_status": row[3]
        }

    # ==========================================================
    # ADMIN PANEL — USERS
    # ==========================================================

    def admin_open_users_list(self, user_id: int):
        rows = self.admin_get_users_list()

        users = []
        for row in rows:
            users.append({
                "id": row[0],
                "name": row[1]
            })

        message = self.formatter.build_admin_users_list_message(users)

        return {
            "message": message,
            "keyboard": self.get_admin_users_keyboard()
        }

    def admin_open_user_details(self, target_user_id: int, admin_id: int):
        user = self.admin_get_user_details(target_user_id)

        if user is None:
            return {
                "message": "❌ المستخدم غير موجود.",
                "keyboard": self.get_admin_users_keyboard()
            }

        message = self.formatter.build_admin_user_details_message(user)

        return {
            "message": message,
            "keyboard": self.get_admin_user_details_keyboard()
        }

    # ==========================================================
    # ADMIN — SUBSCRIPTIONS PANEL
    # ==========================================================

    def admin_open_subscriptions_panel(self, user_id: int):
        message = self.formatter.build_admin_subscriptions_menu_message()
        keyboard = self.get_admin_subscriptions_keyboard()
        return {"message": message, "keyboard": keyboard}

    def admin_open_subscribers_list(self, user_id: int):
        rows = self.db.get_active_subscribers()
        message = self.formatter.build_admin_subscribers_message(rows)
        keyboard = self.get_admin_subscriptions_keyboard()
        return {"message": message, "keyboard": keyboard}

    def admin_open_expired_subscriptions(self, user_id: int):
        rows = self.db.get_expired_subscriptions()
        message = self.formatter.build_admin_expired_subscriptions_message(rows)
        keyboard = self.get_admin_subscriptions_keyboard()
        return {"message": message, "keyboard": keyboard}

    def admin_open_subscription_logs(self, user_id: int):
        rows = self.db.get_subscription_logs()
        message = self.formatter.build_admin_subscription_logs_message(rows)
        keyboard = self.get_admin_subscriptions_keyboard()
        return {"message": message, "keyboard": keyboard}

    def admin_open_free_trial_settings(self, user_id: int):
        settings = self.db.get_free_trial_settings()
        message = self.formatter.build_admin_free_trial_message(settings)
        keyboard = self.get_admin_subscriptions_keyboard()
        return {"message": message, "keyboard": keyboard}

    def admin_open_subscription_settings(self, user_id: int):
        mode = self.get_subscription_mode()
        message = self.formatter.build_admin_subscription_settings_message(mode)
        keyboard = self.get_admin_subscription_settings_keyboard(mode)
        return {"message": message, "keyboard": keyboard}

    def admin_open_subscription_requests(self):
        """Show only pending requests and per-request guarded actions."""
        rows = self.db.get_manual_subscription_requests()
        message = self.formatter.build_admin_subscription_requests_message(rows)
        keyboard = []
        for request_id, *_rest in rows:
            keyboard.append([
                f"{self.BTN_ADMIN_APPROVE_REQUEST_PREFIX}{request_id}",
                f"{self.BTN_ADMIN_REJECT_REQUEST_PREFIX}{request_id}",
            ])
        keyboard.extend(self.get_admin_subscriptions_keyboard())
        return {"message": message, "keyboard": keyboard}

    @staticmethod
    def _request_id_from_admin_action(button_text: str, prefix: str):
        try:
            return int(button_text.removeprefix(prefix).strip())
        except ValueError:
            return None

    # ==========================================================
    # ADMIN — KEYBOARDS
    # ==========================================================

    def get_admin_users_keyboard(self):
        return [
            [self.BTN_ADMIN_USERS_LIST],
            [self.BTN_ADMIN_SEARCH_USER],
            [self.BTN_HOME]
        ]

    def get_admin_user_details_keyboard(self):
        return [
            [self.BTN_BACK],
            [self.BTN_ADMIN_USERS_LIST],
            [self.BTN_ADMIN_SEARCH_USER],
            [self.BTN_HOME]
        ]

    def get_admin_subscriptions_keyboard(self):
        mode = self.get_subscription_mode()

        keyboard = [
            [self.BTN_ADMIN_SUBSCRIBERS, self.BTN_ADMIN_EXPIRED],
            [self.BTN_ADMIN_LOGS],
            [self.BTN_ADMIN_FREE_TRIAL],
            [self.BTN_ADMIN_SUBS_SETTINGS],
            [self.BTN_BACK],
            [self.BTN_HOME]
        ]

        if mode == "manual":
            keyboard.insert(1, [self.BTN_ADMIN_REQUESTS])

        return keyboard

    def get_admin_subscription_settings_keyboard(self, mode: str):
        if mode == "auto":
            return [
                ["✅ الوضع الحالي: آلي"],
                ["✋ التحويل إلى الوضع اليدوي"],
                [self.BTN_BACK],
                [self.BTN_HOME]
            ]
        else:
            return [
                ["✅ الوضع الحالي: يدوي"],
                ["🔄 التحويل إلى الوضع الآلي"],
                [self.BTN_BACK],
                [self.BTN_HOME]
            ]



    # ==========================================================
    # BUTTON HANDLER — مع إصلاح self.BTN_HOME وجميع الأزرار
    # ==========================================================

    def handle_button(self, button_text: str, first_name: str, user_id: int, card_type: str | None = None):

        # Never rely on hiding a keyboard row as authorization.  Any text can
        # be sent manually to Telegram, so every administrative action is
        # checked again at the routing boundary.
        if self._is_admin_action(button_text) or self.get_user_state(user_id) == "admin_search_user":
            if not self.is_admin(user_id):
                return {
                    "message": self.formatter.build_service_state_message("ADMIN_REQUIRED"),
                    "keyboard": self.get_main_menu(user_id),
                }

        actions = {
            self.BTN_HOME: lambda: (
                self.set_user_menu(user_id, self.MENU_MAIN),
                self.go_home(first_name, user_id)
            )[1],

            self.BTN_MARKET: lambda: self.open_menu(self.MENU_MARKET, user_id),
            self.BTN_OPPORTUNITIES: lambda: self.open_menu(self.MENU_OPPORTUNITIES, user_id),
            self.BTN_NEWS: lambda: self.open_menu(self.MENU_NEWS, user_id),
            self.BTN_REPORTS: lambda: self.open_menu(self.MENU_REPORTS, user_id),
            self.BTN_ANALYSIS: lambda: self.open_menu(self.MENU_ANALYSIS, user_id),
            self.BTN_CHANNEL: lambda: self.open_menu(self.MENU_CHANNEL, user_id),
            self.BTN_SETTINGS: lambda: self.open_menu(self.MENU_SETTINGS, user_id),
            self.BTN_HELP: lambda: self.open_menu(self.MENU_HELP, user_id),

            self.BTN_SUBSCRIPTIONS: lambda: (
                self.set_user_menu(user_id, self.MENU_SUBSCRIPTION_PAGE),
                self.build_subscription_page(user_id)
            )[1],
        }

        # إضافة زر لوحة الإدارة إذا كان المستخدم Admin أو Owner
        if self.is_admin(user_id):
            actions[self.BTN_ADMIN_PANEL] = lambda: self.open_menu(self.MENU_ADMIN, user_id)

        # تنفيذ الإجراء إذا كان الزر موجودًا في القاموس
        if button_text in actions:
            return actions[button_text]()

        # ----------------------------------------------------------
        # USER SERVICE ROUTES — no market/news engine is invoked here
        # unless the underlying result is journal-backed and trustworthy.
        # ----------------------------------------------------------
        if button_text in {self.BTN_INDICES, self.BTN_GOLD, self.BTN_BITCOIN, self.BTN_CALENDAR}:
            return self._service_response("WAITING_FOR_DATA_PROVIDER", user_id)

        if button_text in {self.BTN_SPX, self.BTN_SPY, self.BTN_NASDAQ, self.BTN_QQQ}:
            return self._service_response("WAITING_FOR_DATA_PROVIDER", user_id)

        if button_text in {self.BTN_NEWS_PREMARKET, self.BTN_NEWS_BREAKING, self.BTN_NEWS_AFTER_MARKET}:
            return self._service_response("TEMPORARILY_UNAVAILABLE", user_id)

        if button_text == self.BTN_COMPLETED_TRADES:
            denied = self._subscriber_access_state(user_id)
            if denied:
                return self._service_response(denied, user_id)
            completed = self.db.get_completed_trade_summaries()
            if not completed:
                return self._service_response("NO_RESULTS", user_id)
            lines = ["🏆 الصفقات المكتملة\n"]
            for trade in completed:
                lines.append(
                    f"• {trade['symbol']} — {trade.get('direction') or '—'}\n"
                    f"  أغلقت: {trade.get('closed_at') or 'غير متاح'}"
                )
            return {"message": "\n".join(lines), "keyboard": self.OPPORTUNITIES_MENU}

        if button_text == self.BTN_DAILY_REPORT:
            denied = self._subscriber_access_state(user_id)
            if denied:
                return self._service_response(denied, user_id)
            from performance_engine import PerformanceEngine
            report = PerformanceEngine(journal=self.db).get_daily_report()
            if not report.get("total_trades"):
                return self._service_response("NO_RESULTS", user_id)
            return {
                "message": (
                    "📅 التقرير اليومي\n\n"
                    f"إجمالي الإشارات المسجلة: {report['total_trades']}\n"
                    f"TP1: {report['tp1']} | TP2: {report['tp2']} | TP3: {report['tp3']}\n"
                    f"وقف الخسارة: {report['stop_loss']} | الصفقات المغلقة: {report['completed']}\n\n"
                    "يعرض هذا الملخص أحداثًا مسجلة فقط."
                ),
                "keyboard": self.REPORTS_MENU,
            }

        if button_text in {self.BTN_WEEKLY_REPORT, self.BTN_MONTHLY_REPORT}:
            return self._service_response("COMING_SOON", user_id)

        if button_text in {self.BTN_LANGUAGE, self.BTN_NOTIFICATIONS, self.BTN_FAQ}:
            return self._service_response("COMING_SOON", user_id)

        if button_text == self.BTN_GUIDE:
            return {"message": self.formatter.build_help_message(), "keyboard": self.HELP_MENU}

        if button_text == self.BTN_ABOUT:
            return {"message": self.formatter.build_welcome_message(first_name), "keyboard": self.HELP_MENU}

        # ADMIN PANEL — BUTTONS

        if button_text == self.BTN_ADMIN_USERS_LIST:
            return self.admin_open_users_list(user_id)

        if button_text == self.BTN_ADMIN_SEARCH_USER:
            self.set_user_state(user_id, "admin_search_user")
            return {
                "message": "🔎 أرسل الآن الـ ID أو الـ Username للبحث عنه.",
                "keyboard": self.get_admin_users_keyboard()
            }

        if self.get_user_state(user_id) == "admin_search_user":
            user = self.admin_search_user(button_text)
            self.set_user_state(user_id, None)

            if user is None:
                return {
                    "message": "❌ لم يتم العثور على أي مستخدم بهذا المعرف.",
                    "keyboard": self.get_admin_users_keyboard()
                }

            return self.admin_open_user_details(user["user_id"], user_id)

        if button_text.startswith("المستخدم رقم"):
            try:
                target_id_part = button_text.split("المستخدم رقم", 1)[1]
                target_id = int(target_id_part.split("—")[0].strip())
                return self.admin_open_user_details(target_id, user_id)
            except ValueError:
                return {
                    "message": "❌ حدث خطأ أثناء قراءة رقم المستخدم.",
                    "keyboard": self.get_admin_users_keyboard()
                }

        # ADMIN — SUBSCRIPTIONS PANEL

        if button_text == self.BTN_ADMIN_SUBSCRIPTIONS:
            self.set_user_menu(user_id, self.MENU_ADMIN_SUBSCRIPTIONS)
            return self.admin_open_subscriptions_panel(user_id)

        if button_text == self.BTN_ADMIN_SUBSCRIBERS:
            return self.admin_open_subscribers_list(user_id)

        if button_text == self.BTN_ADMIN_EXPIRED:
            return self.admin_open_expired_subscriptions(user_id)

        if button_text == self.BTN_ADMIN_LOGS:
            return self.admin_open_subscription_logs(user_id)

        if button_text == self.BTN_ADMIN_FREE_TRIAL:
            return self.admin_open_free_trial_settings(user_id)

        if button_text == self.BTN_ADMIN_SUBS_SETTINGS:
            return self.admin_open_subscription_settings(user_id)

        if button_text == self.BTN_ADMIN_REQUESTS:
            return self.admin_open_subscription_requests()

        if button_text.startswith(self.BTN_ADMIN_APPROVE_REQUEST_PREFIX):
            request_id = self._request_id_from_admin_action(
                button_text, self.BTN_ADMIN_APPROVE_REQUEST_PREFIX
            )
            success = bool(request_id is not None and self.db.approve_request(request_id))
            return {
                "message": self.formatter.build_subscription_request_action_message(
                    "approve", request_id or 0, success
                ),
                "keyboard": self.get_admin_subscriptions_keyboard(),
            }

        if button_text.startswith(self.BTN_ADMIN_REJECT_REQUEST_PREFIX):
            request_id = self._request_id_from_admin_action(
                button_text, self.BTN_ADMIN_REJECT_REQUEST_PREFIX
            )
            success = bool(request_id is not None and self.db.reject_request(request_id))
            return {
                "message": self.formatter.build_subscription_request_action_message(
                    "reject", request_id or 0, success
                ),
                "keyboard": self.get_admin_subscriptions_keyboard(),
            }

        # SUBSCRIPTIONS — ACTION BUTTONS

        if button_text == self.BTN_SUBS_RENEW:
            self.set_user_menu(user_id, self.MENU_SUBSCRIPTION_PAGE)
            return self.build_subscription_page(user_id)

        if button_text == self.BTN_SUBS_RESEND_INVITE:
            access_state = self._subscriber_access_state(user_id)
            if access_state:
                return self._service_response(access_state, user_id)
            message = self.formatter.build_subscription_invite_unavailable_message()
            keyboard = [
                [self.BTN_BACK],
                [self.BTN_HOME]
            ]
            return {"message": message, "keyboard": keyboard}

        if button_text == self.BTN_SUBS_GO_TO_STORE:
            return self._service_response("COMING_SOON", user_id)

        plan_buttons = {
            self.BTN_SUBS_REQUEST_BIWEEKLY: InterfaceFormatter.PLAN_BIWEEKLY,
            self.BTN_SUBS_REQUEST_MONTHLY: InterfaceFormatter.PLAN_MONTHLY,
        }
        if button_text in plan_buttons:
            result = self.db.create_subscription_request_by_tg_id(user_id, plan_buttons[button_text])
            if result.get("created"):
                return {
                    "message": self.formatter.build_subscription_request_created_message(),
                    "keyboard": [[self.BTN_HOME]],
                }
            if result.get("reason") == "pending_exists":
                return {
                    "message": self.formatter.build_subscription_request_pending_message(),
                    "keyboard": [[self.BTN_HOME]],
                }
            return self._service_response("TEMPORARILY_UNAVAILABLE", user_id)

        # NAVIGATION BUTTONS

        if button_text == self.BTN_BACK:
            current_menu = self.get_user_menu(user_id)

            if current_menu == self.MENU_SUBSCRIPTION_PAGE:
                return self.open_main_page(first_name, user_id)

            if current_menu == self.MENU_ADMIN_SUBSCRIPTIONS:
                return self.open_menu(self.MENU_ADMIN, user_id)

            return self.go_home(first_name, user_id)

        if button_text == self.BTN_HOME:
            self.set_user_menu(user_id, self.MENU_MAIN)
            return self.go_home(first_name, user_id)

        # FALLBACK

        return self.go_home(first_name, user_id)

    def _service_response(self, state: str, user_id: int):
        return {
            "message": self.formatter.build_service_state_message(state),
            "keyboard": self.get_keyboard_layout(self.get_user_menu(user_id), user_id),
        }


    # ==========================================================
    # NAVIGATION ENGINE
    # ==========================================================

    HOME_BUTTON = BTN_HOME
    BACK_BUTTON = BTN_BACK

    def is_home_button(self, button_text: str) -> bool:
        return button_text == self.HOME_BUTTON

    def is_back_button(self, button_text: str) -> bool:
        return button_text == self.BACK_BUTTON

    def can_open_admin(self, user_id: int) -> bool:
        return self.is_admin(user_id)

    def validate_menu(self, menu_name: str) -> bool:
        valid_menus = {
            self.MENU_MAIN,
            self.MENU_MARKET,
            self.MENU_OPPORTUNITIES,
            self.MENU_NEWS,
            self.MENU_REPORTS,
            self.MENU_ANALYSIS,
            self.MENU_CHANNEL,
            self.MENU_SETTINGS,
            self.MENU_HELP,
            self.MENU_ADMIN,
            self.MENU_ADMIN_SUBSCRIPTIONS
        }
        return menu_name in valid_menus

