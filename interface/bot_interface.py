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

    # 🔥 هذا السطر الصحيح 100٪ — داخل الكلاس وليس خارجه
    print("🔥 BotInterface LOADED FROM:", __file__)

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

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self, channel_url: str, db):
        self.channel_url = channel_url
        self.db = db

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
        return self.db.get_user_role(user_id)

    def is_admin(self, user_id: int) -> bool:
        return self.get_user_role(user_id) in ("owner", "admin")

    def is_owner(self, user_id: int) -> bool:
        return self.get_user_role(user_id) == "owner"

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
        ["📊 المؤشرات"],
        ["🥇 الذهب", "₿ البيتكوين"],
        ["📅 التقويم الاقتصادي"],
        [BTN_HOME]
    ]

    OPPORTUNITIES_MENU = [
        ["🏆 الصفقات المكتملة"],
        [BTN_HOME]
    ]

    NEWS_MENU = [
        ["🌅 ما قبل الافتتاح"],
        ["🚨 الأخبار العاجلة"],
        ["🌙 بعد الإغلاق"],
        [BTN_HOME]
    ]

    REPORTS_MENU = [
        ["📅 التقرير اليومي"],
        ["📈 التقرير الأسبوعي"],
        ["📊 التقرير الشهري"],
        [BTN_HOME]
    ]

    ANALYSIS_MENU = [
        ["📈 SPX", "📊 SPY"],
        ["💻 NASDAQ", "📉 QQQ"],
        [BTN_HOME]
    ]

    SETTINGS_MENU = [
        ["🌐 اللغة"],
        ["🔔 الإشعارات"],
        [BTN_HOME]
    ]

    HELP_MENU = [
        ["📖 دليل الاستخدام"],
        ["❓ الأسئلة الشائعة"],
        ["ℹ️ حول البوت"],
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
        return {
            "message": self.get_menu_message(menu_name),
            "keyboard": self.get_keyboard_layout(menu_name, user_id)
        }

    # ==========================================================
    # SUBSCRIPTIONS — SMART PAGE
    # ==========================================================

    def get_subscription_mode(self) -> str:
        return self.db.get_subscription_mode()

    def set_subscription_mode(self, mode: str):
        self.db.set_subscription_mode(mode)

    def get_user_subscription(self, user_id: int):
        return self.db.get_user_subscription(user_id)

    def build_subscription_page(self, user_id: int):
        subscription = self.get_user_subscription(user_id)

        if subscription is None or subscription.get("status") == "none":
            message = self.formatter.build_subscription_plans_message()
            keyboard = [
                [BTN_SUBS_GO_TO_STORE],
                [BTN_BACK],
                [BTN_HOME]
            ]
            return {"message": message, "keyboard": keyboard}

        status = subscription.get("status")

        if status == "active":
            message = self.formatter.build_subscription_status_message(subscription)
            keyboard = [
                [BTN_SUBS_RENEW, BTN_SUBS_RESEND_INVITE],
                [BTN_BACK],
                [BTN_HOME]
            ]
            return {"message": message, "keyboard": keyboard}

        message = self.formatter.build_subscription_expired_message(subscription)
        keyboard = [
            [BTN_SUBS_RENEW, BTN_SUBS_GO_TO_STORE],
            [BTN_BACK],
            [BTN_HOME]
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
            rows = self.db.get_manual_subscription_requests()
            message = self.formatter.build_admin_subscription_requests_message(rows)
            keyboard = self.get_admin_subscriptions_keyboard()
            return {"message": message, "keyboard": keyboard}

        # SUBSCRIPTIONS — ACTION BUTTONS

        if button_text == self.BTN_SUBS_RENEW:
            message = self.formatter.build_subscription_renew_placeholder_message()
            keyboard = [
                [self.BTN_BACK],
                [self.BTN_HOME]
            ]
            return {"message": message, "keyboard": keyboard}

        if button_text == self.BTN_SUBS_RESEND_INVITE:
            message = self.formatter.build_subscription_resend_invite_placeholder_message()
            keyboard = [
                [self.BTN_BACK],
                [self.BTN_HOME]
            ]
            return {"message": message, "keyboard": keyboard}

        if button_text == self.BTN_SUBS_GO_TO_STORE:
            message = self.formatter.build_subscription_store_message()
            keyboard = [
                [self.BTN_BACK],
                [self.BTN_HOME]
            ]
            return {"message": message, "keyboard": keyboard}

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

        return {
            "message": self.formatter.build_under_development_message(),
            "keyboard": self.get_keyboard_layout(self.get_user_menu(user_id), user_id)
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

