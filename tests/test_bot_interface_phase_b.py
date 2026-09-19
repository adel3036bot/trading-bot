from __future__ import annotations

import sqlite3
import unittest
from datetime import timedelta

from database.database import DatabaseManager
from interface.bot_interface import BotInterface
from telegram_bot.telegram_app import TelegramApp


class _Db:
    def __init__(self, role="user", subscription="none"):
        self.role, self.subscription = role, subscription

    def get_user_role(self, _tg_id, *, owner_tg_id=None):
        return "owner" if _tg_id == owner_tg_id else self.role

    def add_user(self, *_args):
        return None

    def update_user_activity(self, *_args):
        return None

    def get_user_subscription_by_tg_id(self, _tg_id):
        return {"status": self.subscription}

    def get_completed_trade_summaries(self):
        return []

    def get_subscription_mode(self):
        return "manual"

    def create_subscription_request_by_tg_id(self, _tg_id, _plan_id):
        return {"created": True, "request_id": 1}


class _SharedMemoryDatabase(DatabaseManager):
    """Diskless database for restart-style tests in the restricted runner."""

    _uri = "file:adel_phase_b_test?mode=memory&cache=shared"
    _keeper = sqlite3.connect(_uri, uri=True, check_same_thread=False)

    def __init__(self):
        self.db_path = self._uri
        self._init_database()

    def connect(self):
        conn = sqlite3.connect(self.db_path, uri=True, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn


class _Chat:
    def __init__(self, chat_type): self.type = chat_type


class _User:
    id = 7
    first_name = "Tester"
    username = "tester"


class _Message:
    def __init__(self, text):
        self.text = text
        self.replies = []

    async def reply_text(self, **kwargs):
        self.replies.append(kwargs)


class _Update:
    def __init__(self, text, chat_type="private"):
        self.message = _Message(text)
        self.effective_chat = _Chat(chat_type)
        self.effective_user = _User()


class BotInterfacePhaseBTests(unittest.IsolatedAsyncioTestCase):
    def make_app(self):
        app = TelegramApp.__new__(TelegramApp)
        app.db = _Db()
        app.interface = BotInterface("https://t.me/ADELSmartSignals", app.db, owner_tg_id=1)
        return app

    async def test_start_and_greetings_open_welcome_then_home(self):
        app = self.make_app()
        for text in ("/start", "مرحبا", "السلام عليكم", "Hi"):
            update = _Update(text)
            if text == "/start":
                await app.start(update, None)
            else:
                await app.handle_button(update, None)
            self.assertEqual(len(update.message.replies), 2)
            self.assertIn("الصفحة الرئيسية", update.message.replies[-1]["text"])

    async def test_unknown_returns_home_and_group_never_gets_keyboard(self):
        app = self.make_app()
        unknown = _Update("anything unknown")
        await app.handle_button(unknown, None)
        self.assertEqual(len(unknown.message.replies), 1)
        self.assertIn("الصفحة الرئيسية", unknown.message.replies[0]["text"])
        group = _Update("/start", chat_type="group")
        await app.start(group, None)
        self.assertEqual(group.message.replies, [])

    def test_home_admin_guard_and_service_states(self):
        interface = BotInterface("https://t.me/ADELSmartSignals", _Db(), owner_tg_id=1)
        self.assertIn("الصفحة الرئيسية", interface.handle_button(interface.BTN_HOME, "Tester", 7)["message"])
        self.assertIn("مخصصة للإدارة", interface.handle_button(interface.BTN_ADMIN_USERS_LIST, "Tester", 7)["message"])
        self.assertIn("البيانات المباشرة", interface.handle_button(interface.BTN_GOLD, "Tester", 7)["message"])
        self.assertIn("🔒", interface.handle_button(interface.BTN_COMPLETED_TRADES, "Tester", 7)["message"])

    def test_all_main_menus_and_subscription_access_states(self):
        interface = BotInterface("https://t.me/ADELSmartSignals", _Db(), owner_tg_id=1)
        expected = {
            interface.BTN_MARKET: interface.MENU_MARKET,
            interface.BTN_OPPORTUNITIES: interface.MENU_OPPORTUNITIES,
            interface.BTN_NEWS: interface.MENU_NEWS,
            interface.BTN_REPORTS: interface.MENU_REPORTS,
            interface.BTN_ANALYSIS: interface.MENU_ANALYSIS,
            interface.BTN_CHANNEL: interface.MENU_CHANNEL,
            interface.BTN_SETTINGS: interface.MENU_SETTINGS,
            interface.BTN_HELP: interface.MENU_HELP,
        }
        for button, menu in expected.items():
            interface.handle_button(button, "Tester", 7)
            self.assertEqual(interface.get_user_menu(7), menu)
        self.assertIn("الصفحة الرئيسية", interface.handle_button(interface.BTN_HOME, "Tester", 7)["message"])

        expired = BotInterface("https://t.me/ADELSmartSignals", _Db(subscription="expired"), owner_tg_id=1)
        self.assertIn("انتهى اشتراكك", expired.handle_button(expired.BTN_DAILY_REPORT, "Tester", 7)["message"])

        subscriber = BotInterface("https://t.me/ADELSmartSignals", _Db(subscription="active"), owner_tg_id=1)
        self.assertIn("لا توجد نتائج", subscriber.handle_button(subscriber.BTN_COMPLETED_TRADES, "Tester", 7)["message"])

        owner = BotInterface("https://t.me/ADELSmartSignals", _Db(), owner_tg_id=1)
        self.assertIn("لوحة الإدارة", owner.handle_button(owner.BTN_ADMIN_PANEL, "Owner", 1)["message"])

    def test_channel_is_named_html_link(self):
        interface = BotInterface("https://t.me/ADELSmartSignals", _Db(), owner_tg_id=1)
        page = interface.open_menu(interface.MENU_CHANNEL, user_id=7)
        self.assertEqual(page["parse_mode"], "HTML")
        self.assertIn('<a href="https://t.me/ADELSmartSignals">📢 ADEL Smart Signals</a>', page["message"])

    def test_submenu_routes_return_honest_states_not_dead_buttons(self):
        interface = BotInterface("https://t.me/ADELSmartSignals", _Db(), owner_tg_id=1)
        self.assertIn("⏳", interface.handle_button(interface.BTN_INDICES, "Tester", 7)["message"])
        self.assertIn("⏳", interface.handle_button(interface.BTN_SPX, "Tester", 7)["message"])
        self.assertIn("⚠️", interface.handle_button(interface.BTN_NEWS_PREMARKET, "Tester", 7)["message"])
        self.assertIn("🚧", interface.handle_button(interface.BTN_WEEKLY_REPORT, "Tester", 7)["message"])
        self.assertIn("🚧", interface.handle_button(interface.BTN_LANGUAGE, "Tester", 7)["message"])
        self.assertIn("دليل الاستخدام", interface.handle_button(interface.BTN_GUIDE, "Tester", 7)["message"])

    def test_subscription_mapping_request_and_restart_persistence(self):
        db = _SharedMemoryDatabase()
        db.add_user(7001, "Subscriber", "subscriber")
        db.add_user(7002, "Guest", "guest")
        user_id = db.get_internal_user_id(7001)
        conn = db.connect()
        conn.execute("INSERT OR IGNORE INTO plans (id, name, duration_days, price) VALUES (1, 'Biweekly', 14, 0)")
        conn.commit()
        conn.close()
        today = db.now().date()
        db.create_subscription(user_id, 1, today.isoformat(), (today + timedelta(days=2)).isoformat())
        self.assertEqual(db.get_user_subscription_by_tg_id(7001)["status"], "active")
        self.assertTrue(db.is_subscription_active_by_tg_id(7001))
        request = db.create_subscription_request_by_tg_id(7002, 1)
        self.assertTrue(request["created"])
        restarted = _SharedMemoryDatabase()
        self.assertEqual(restarted.get_user_subscription_by_tg_id(7001)["status"], "active")
        self.assertEqual(restarted.create_subscription_request_by_tg_id(7002, 1)["reason"], "pending_exists")

    def test_manual_approval_rejection_invite_access_and_restart(self):
        db = _SharedMemoryDatabase()
        owner_id, guest_id, rejected_id, expired_id = 8100, 8101, 8102, 8103
        for tg_id, name in (
            (guest_id, "Guest"),
            (rejected_id, "Rejected"),
            (expired_id, "Expired"),
        ):
            db.add_user(tg_id, name, name.lower())

        conn = db.connect()
        conn.execute(
            "INSERT OR IGNORE INTO plans (id, name, duration_days, price) VALUES (1, 'Biweekly', 14, 0)"
        )
        conn.execute(
            "INSERT OR IGNORE INTO plans (id, name, duration_days, price) VALUES (99, 'Manual', 30, 0)"
        )
        conn.commit()
        conn.close()

        guest_ui = BotInterface("https://t.me/ADELSmartSignals", db, owner_tg_id=owner_id)
        owner_ui = BotInterface("https://t.me/ADELSmartSignals", db, owner_tg_id=owner_id)

        request_page = guest_ui.handle_button(
            guest_ui.BTN_SUBS_REQUEST_BIWEEKLY, "Guest", guest_id
        )
        self.assertIsInstance(request_page["message"], str)
        request_id = db.get_manual_subscription_requests()[0][0]
        self.assertEqual(
            db.create_subscription_request_by_tg_id(guest_id, 1)["reason"], "pending_exists"
        )

        pending = owner_ui.handle_button(owner_ui.BTN_ADMIN_REQUESTS, "Owner", owner_id)
        self.assertIn(str(request_id), pending["message"])
        approve_button = f"{owner_ui.BTN_ADMIN_APPROVE_REQUEST_PREFIX}{request_id}"
        self.assertTrue(any(approve_button in row for row in pending["keyboard"]))

        denied = guest_ui.handle_button(approve_button, "Guest", guest_id)
        self.assertIn("مخصصة للإدارة", denied["message"])
        self.assertEqual(db.get_subscription_request(request_id)["status"], "pending")

        approved = owner_ui.handle_button(approve_button, "Owner", owner_id)
        self.assertIn("تم قبول", approved["message"])
        self.assertEqual(db.get_subscription_request(request_id)["status"], "approved")
        self.assertEqual(db.get_user_subscription_by_tg_id(guest_id)["status"], "active")
        logs = db.get_subscription_logs()
        self.assertTrue(any(row[2] == "approve_request" for row in logs))
        repeated = owner_ui.handle_button(approve_button, "Owner", owner_id)
        self.assertIn("لم يعد معلقًا", repeated["message"])

        rejected = db.create_subscription_request_by_tg_id(rejected_id, 99)
        reject_button = f"{owner_ui.BTN_ADMIN_REJECT_REQUEST_PREFIX}{rejected['request_id']}"
        reject_result = owner_ui.handle_button(reject_button, "Owner", owner_id)
        self.assertIn("تم رفض", reject_result["message"])
        self.assertEqual(
            db.get_subscription_request(rejected["request_id"])["status"], "rejected"
        )
        self.assertTrue(any(row[2] == "reject_request" for row in db.get_subscription_logs()))

        expired_internal_id = db.get_internal_user_id(expired_id)
        yesterday = db.now().date() - timedelta(days=1)
        db.create_subscription(expired_internal_id, 99, yesterday.isoformat(), yesterday.isoformat())
        self.assertEqual(db.get_user_subscription_by_tg_id(expired_id)["status"], "expired")
        renewal = db.create_subscription_request_by_tg_id(expired_id, 99)
        self.assertTrue(renewal["created"])

        invite_active = guest_ui.handle_button(guest_ui.BTN_SUBS_RESEND_INVITE, "Guest", guest_id)
        self.assertIn("غير متاح", invite_active["message"])
        invite_guest = guest_ui.handle_button(guest_ui.BTN_SUBS_RESEND_INVITE, "Guest", rejected_id)
        self.assertIn("الاشتراك", invite_guest["message"])
        invite_expired = guest_ui.handle_button(guest_ui.BTN_SUBS_RESEND_INVITE, "Expired", expired_id)
        self.assertIn("انتهى اشتراكك", invite_expired["message"])

        restarted = _SharedMemoryDatabase()
        self.assertEqual(restarted.get_subscription_request(request_id)["status"], "approved")
        self.assertEqual(restarted.get_subscription_request(rejected["request_id"])["status"], "rejected")
        self.assertEqual(restarted.get_user_subscription_by_tg_id(guest_id)["status"], "active")


if __name__ == "__main__":
    unittest.main()
