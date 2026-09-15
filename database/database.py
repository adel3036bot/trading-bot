# ==========================================================
# ADEL SMART BOT ELITE
# Database Manager — Phase 1 (Final 10/10)
# ==========================================================

import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo


class DatabaseManager:
    """
    المرحلة الأولى:
    - إنشاء الجداول الأساسية
    - تفعيل القيود المرجعية
    - إضافة NOT NULL للأعمدة الأساسية
    - إضافة قيم افتراضية للحالات
    - إضافة فهارس لتحسين الأداء
    """

    def __init__(self, db_path="adel_smart_bot.db"):
        self.db_path = db_path
        self._init_database()

    # ==========================================================
    # TIME HANDLER — توقيت السعودية
    # ==========================================================

    def now(self):
        return datetime.now(ZoneInfo("Asia/Riyadh"))

    # ==========================================================
    # INTERNAL — CONNECTION
    # ==========================================================

    def connect(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON;")  # تفعيل القيود المرجعية
        return conn

    # ==========================================================
    # INITIAL TABLE CREATION — المرحلة الأولى
    # ==========================================================

    def _init_database(self):
        conn = self.connect()
        cur = conn.cursor()

        # جدول المستخدمين
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE NOT NULL,
                first_name TEXT,
                username TEXT,
                join_date TEXT,
                last_activity TEXT,
                subscription_status TEXT DEFAULT 'inactive',
                usage_count INTEGER DEFAULT 0
            )
        """)

        # فهرس للبحث السريع
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_tg_id ON users(tg_id);")

        # جدول الباقات (إضافة UNIQUE لاسم الباقة)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                duration_days INTEGER NOT NULL,
                price REAL NOT NULL
            )
        """)

        # جدول الاشتراكات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(plan_id) REFERENCES plans(id)
            )
        """)

        # فهرس المستخدم داخل الاشتراكات
        cur.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);")

        # فهرس حالة الاشتراكات (تحسين الأداء)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);")

        # جدول طلبات الاشتراك
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscription_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id INTEGER NOT NULL,
                request_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY(user_id) REFERENCES users(id),
                FOREIGN KEY(plan_id) REFERENCES plans(id)
            )
        """)

        # فهرس المستخدم داخل الطلبات
        cur.execute("CREATE INDEX IF NOT EXISTS idx_requests_user_id ON subscription_requests(user_id);")

        # فهرس حالة الطلبات (مهم للوحة الإدارة)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_requests_status ON subscription_requests(status);")

        # جدول سجل العمليات
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscription_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                date TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)

        # جدول الإعدادات العامة
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        conn.commit()
        conn.close()

    # ==========================================================
    # ADD USER — إضافة مستخدم جديد (مع حماية UNIQUE)
    # ==========================================================

    def add_user(self, tg_id, first_name, username):
        """
        إضافة مستخدم جديد إذا لم يكن موجودًا مسبقًا.
        حماية UNIQUE على tg_id تمنع التكرار.
        """

        conn = self.connect()
        cur = conn.cursor()

        # التحقق من وجود المستخدم مسبقًا
        cur.execute("SELECT id FROM users WHERE tg_id = ?", (tg_id,))
        row = cur.fetchone()

        if row:
            # المستخدم موجود → لا نضيفه مرة أخرى
            conn.close()
            return

        # المستخدم غير موجود → نضيفه
        cur.execute("""
            INSERT INTO users (tg_id, first_name, username, join_date, last_activity, subscription_status, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            tg_id,
            first_name,
            username,
            self.now().isoformat(),
            self.now().isoformat(),
            "inactive",
            0
        ))

        conn.commit()
        conn.close()

    # ==========================================================
    # USER ACTIVITY MANAGEMENT — تحديث نشاط المستخدم
    # ==========================================================

    def update_user_activity(self, tg_id):
        """
        تحديث آخر نشاط المستخدم + زيادة عدّاد الاستخدام.
        يعتمد على tg_id لأن TelegramApp يمرّر user.id (وهو Telegram ID).
        """

        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            UPDATE users
            SET last_activity = ?, usage_count = usage_count + 1
            WHERE tg_id = ?
        """, (
            self.now().isoformat(),
            tg_id
        ))

        conn.commit()
        conn.close()


    # ==========================================================
    # PHASE 2 — SUBSCRIPTION CORE FUNCTIONS (FIXED LOGIC)
    # ==========================================================

    def create_subscription(self, user_id, plan_id, start_date, end_date):
        """
        إنشاء اشتراك جديد للمستخدم.
        الفلسفة:
        - لا يسمح بوجود أكثر من اشتراك نشط لنفس المستخدم.
        - إذا وجد اشتراك نشط، يتم إنهاؤه أولاً ثم إنشاء الجديد (تجديد).
        """
        conn = self.connect()
        cur = conn.cursor()

        # إنهاء أي اشتراك نشط سابق
        cur.execute("""
            SELECT id FROM subscriptions
            WHERE user_id = ? AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))
        row = cur.fetchone()

        if row:
            old_sub_id = row[0]
            cur.execute("""
                UPDATE subscriptions
                SET status = 'expired'
                WHERE id = ?
            """, (old_sub_id,))

        # إنشاء الاشتراك الجديد
        cur.execute("""
            INSERT INTO subscriptions (user_id, plan_id, start_date, end_date, status)
            VALUES (?, ?, ?, ?, 'active')
        """, (user_id, plan_id, start_date, end_date))

        # تحديث حالة المستخدم
        cur.execute("""
            UPDATE users
            SET subscription_status = 'active'
            WHERE id = ?
        """, (user_id,))

        conn.commit()
        conn.close()

    # ----------------------------------------------------------

    def get_active_subscription(self, user_id):
        """
        جلب الاشتراك الحالي للمستخدم (إن وجد).
        """
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, plan_id, start_date, end_date, status
            FROM subscriptions
            WHERE user_id = ? AND status = 'active'
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))

        row = cur.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "plan_id": row[1],
            "start_date": row[2],
            "end_date": row[3],
            "status": row[4]
        }

    # ----------------------------------------------------------

    def expire_subscription(self, subscription_id):
        """
        إنهاء الاشتراك عند انتهاء المدة.
        يحصل على user_id من قاعدة البيانات مباشرة
        لتفادي تمرير بيانات غير متطابقة.
        """
        conn = self.connect()
        cur = conn.cursor()

        # جلب المستخدم المرتبط بالاشتراك
        cur.execute("""
            SELECT user_id FROM subscriptions
            WHERE id = ?
        """, (subscription_id,))
        row = cur.fetchone()

        if not row:
            conn.close()
            return

        user_id = row[0]

        # تحديث حالة الاشتراك
        cur.execute("""
            UPDATE subscriptions
            SET status = 'expired'
            WHERE id = ?
        """, (subscription_id,))

        # تحديث حالة المستخدم
        cur.execute("""
            UPDATE users
            SET subscription_status = 'expired'
            WHERE id = ?
        """, (user_id,))

        conn.commit()
        conn.close()

    # ----------------------------------------------------------

    def update_subscription_status(self, user_id, status):
        """
        تحديث حالة الاشتراك داخل جدول users.
        """
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            UPDATE users
            SET subscription_status = ?
            WHERE id = ?
        """, (status, user_id))

        conn.commit()
        conn.close()

    # ----------------------------------------------------------

    def is_subscription_active(self, user_id):
        """
        التحقق من صلاحية الاشتراك.
        - إذا انتهى الاشتراك، يتم تحديث حالته إلى expired
          وتحديث users.subscription_status أيضًا.
        """
        sub = self.get_active_subscription(user_id)
        if not sub:
            return False

        now = self.now().strftime("%Y-%m-%d")

        if now <= sub["end_date"]:
            return True

        # الاشتراك منتهي فعليًا → تحديث الحالة في قاعدة البيانات
        conn = self.connect()
        cur = conn.cursor()

        # تحديث الاشتراك
        cur.execute("""
            UPDATE subscriptions
            SET status = 'expired'
            WHERE id = ?
        """, (sub["id"],))

        # تحديث المستخدم
        cur.execute("""
            UPDATE users
            SET subscription_status = 'expired'
            WHERE id = ?
        """, (user_id,))

        conn.commit()
        conn.close()

        return False

    # ----------------------------------------------------------

    def get_subscription_by_user(self, user_id):
        """
        جلب جميع اشتراكات المستخدم (للسجل).
        """
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, plan_id, start_date, end_date, status
            FROM subscriptions
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,))

        rows = cur.fetchall()
        conn.close()

        return [
            {
                "id": r[0],
                "plan_id": r[1],
                "start_date": r[2],
                "end_date": r[3],
                "status": r[4]
            }
            for r in rows
        ]

    # ==========================================================
    # PHASE 3 — PLANS MANAGEMENT (FINAL FIXED VERSION)
    # ==========================================================

    def add_plan(self, name, duration_days, price):
        """
        إضافة باقة جديدة.
        - يمنع تكرار اسم الباقة.
        - إذا كانت الباقة موجودة، يرجع False.
        """

        conn = self.connect()
        cur = conn.cursor()

        # التحقق من وجود باقة بنفس الاسم
        cur.execute("""
            SELECT id FROM plans
            WHERE LOWER(name) = LOWER(?)
        """, (name,))
        row = cur.fetchone()

        if row:
            conn.close()
            return False  # الباقة موجودة مسبقًا

        # محاولة الإدخال (مع حماية UNIQUE)
        try:
            cur.execute("""
                INSERT INTO plans (name, duration_days, price)
                VALUES (?, ?, ?)
            """, (name, duration_days, price))

            conn.commit()
            conn.close()
            return True

        except sqlite3.IntegrityError:
            conn.close()
            return False

    # ----------------------------------------------------------

    def update_plan(self, plan_id, name=None, duration_days=None, price=None):
        """
        تعديل باقة موجودة.
        يتم تعديل فقط القيم المرسلة.
        """

        conn = self.connect()
        cur = conn.cursor()

        if name is not None:
            # منع تكرار الاسم عند التعديل
            cur.execute("""
                SELECT id FROM plans
                WHERE LOWER(name) = LOWER(?) AND id != ?
            """, (name, plan_id))
            if cur.fetchone():
                conn.close()
                return False  # اسم مستخدم مسبقًا

            cur.execute("UPDATE plans SET name = ? WHERE id = ?", (name, plan_id))

        if duration_days is not None:
            cur.execute("UPDATE plans SET duration_days = ? WHERE id = ?", (duration_days, plan_id))

        if price is not None:
            cur.execute("UPDATE plans SET price = ? WHERE id = ?", (price, plan_id))

        conn.commit()
        conn.close()
        return True

    # ----------------------------------------------------------

    def delete_plan(self, plan_id):
        """
        حذف باقة.
        لا يُسمح بالحذف إذا كانت الباقة مستخدمة في اشتراكات.
        """

        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT COUNT(*) FROM subscriptions
            WHERE plan_id = ?
        """, (plan_id,))
        count = cur.fetchone()[0]

        if count > 0:
            conn.close()
            return False  # لا يمكن حذفها

        cur.execute("DELETE FROM plans WHERE id = ?", (plan_id,))

        conn.commit()
        conn.close()
        return True

    # ----------------------------------------------------------

    def get_plan(self, plan_id):
        """
        جلب باقة واحدة.
        """

        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, duration_days, price
            FROM plans
            WHERE id = ?
        """, (plan_id,))

        row = cur.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "id": row[0],
            "name": row[1],
            "duration_days": row[2],
            "price": row[3]
        }

    # ----------------------------------------------------------

    def get_all_plans(self):
        """
        جلب جميع الباقات.
        """

        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, duration_days, price
            FROM plans
            ORDER BY id ASC
        """)

        rows = cur.fetchall()
        conn.close()

        return [
            {
                "id": r[0],
                "name": r[1],
                "duration_days": r[2],
                "price": r[3]
            }
            for r in rows
        ]

    # ----------------------------------------------------------

    def get_plan_duration(self, plan_id):
        """
        جلب مدة الباقة.
        """

        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT duration_days
            FROM plans
            WHERE id = ?
        """, (plan_id,))

        row = cur.fetchone()
        conn.close()

        return row[0] if row else None

    # ----------------------------------------------------------

    def get_plan_price(self, plan_id):
        """
        جلب سعر الباقة.
        """

        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT price
            FROM plans
            WHERE id = ?
        """, (plan_id,))

        row = cur.fetchone()
        conn.close()

        return row[0] if row else None

    def approve_request(self, request_id):
        """
        قبول الطلب:
        - يجب أن يكون الطلب pending
        - تحديث حالة الطلب إلى approved
        - إنشاء الاشتراك عبر create_subscription()
        - إذا فشل إنشاء الاشتراك، يتم إعادة حالة الطلب إلى pending
        - تسجيل العملية في السجل فقط عند النجاح
        """

        conn = self.connect()
        cur = conn.cursor()

        # جلب بيانات الطلب
        cur.execute("""
            SELECT user_id, plan_id, status
            FROM subscription_requests
            WHERE id = ?
        """, (request_id,))
        row = cur.fetchone()

        if not row:
            conn.close()
            return False

        user_id, plan_id, status = row

        # الطلب يجب أن يكون pending
        if status != "pending":
            conn.close()
            return False

        # تحديث حالة الطلب مبدئيًا إلى approved
        cur.execute("""
            UPDATE subscription_requests
            SET status = 'approved'
            WHERE id = ?
        """, (request_id,))

        # حساب مدة الاشتراك
        duration = self.get_plan_duration(plan_id)
        if duration is None:
            # باقة غير صالحة → إعادة حالة الطلب إلى pending
            cur.execute("""
                UPDATE subscription_requests
                SET status = 'pending'
                WHERE id = ?
            """, (request_id,))
            conn.commit()
            conn.close()
            return False

        from datetime import timedelta
        start_date = self.now().strftime("%Y-%m-%d")
        end_date = (self.now() + timedelta(days=duration)).strftime("%Y-%m-%d")

        # محاولة إنشاء الاشتراك عبر الدالة الرسمية
        try:
            self.create_subscription(user_id, plan_id, start_date, end_date)
        except Exception:
            # فشل إنشاء الاشتراك → إعادة حالة الطلب إلى pending
            cur.execute("""
                UPDATE subscription_requests
                SET status = 'pending'
                WHERE id = ?
            """, (request_id,))
            conn.commit()
            conn.close()
            return False

        # تسجيل العملية فقط عند النجاح
        log_date = self.now().strftime("%Y-%m-%d %H:%M")
        cur.execute("""
            INSERT INTO subscription_logs (user_id, action, date, details)
            VALUES (?, 'approve_request', ?, ?)
        """, (user_id, log_date, f"تم قبول طلب الاشتراك رقم {request_id}"))

        conn.commit()
        conn.close()
        return True

    # ==========================================================
    # PHASE 5 — SUBSCRIPTION LOGS
    # ==========================================================

    def add_log(self, user_id, action, details=""):
        """
        تسجيل عملية جديدة في السجل.
        """
        conn = self.connect()
        cur = conn.cursor()

        log_date = self.now().strftime("%Y-%m-%d %H:%M")

        cur.execute("""
            INSERT INTO subscription_logs (user_id, action, date, details)
            VALUES (?, ?, ?, ?)
        """, (user_id, action, log_date, details))

        conn.commit()
        conn.close()

    # ----------------------------------------------------------

    def get_logs(self):
        """
        جلب جميع السجلات (للإدارة).
        """
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, user_id, action, date, details
            FROM subscription_logs
            ORDER BY id DESC
        """)

        rows = cur.fetchall()
        conn.close()

        return [
            {
                "id": r[0],
                "user_id": r[1],
                "action": r[2],
                "date": r[3],
                "details": r[4]
            }
            for r in rows
        ]

    # ----------------------------------------------------------

    def get_user_logs(self, user_id):
        """
        جلب سجل مستخدم معيّن.
        """
        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, action, date, details
            FROM subscription_logs
            WHERE user_id = ?
            ORDER BY id DESC
        """, (user_id,))

        rows = cur.fetchall()
        conn.close()

        return [
            {
                "id": r[0],
                "action": r[1],
                "date": r[2],
                "details": r[3]
            }
            for r in rows
        ]

    # ==========================================================
    # PHASE 6 — SUBSCRIPTION SETTINGS & FREE TRIAL
    # ==========================================================

    def set_setting(self, key, value):
        """
        تعيين قيمة إعداد داخل جدول settings.
        إذا كان المفتاح موجودًا → تحديثه.
        إذا لم يكن موجودًا → إنشاؤه.
        """

        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))

        conn.commit()
        conn.close()

    # ----------------------------------------------------------

    def get_setting(self, key, default=None):
        """
        جلب قيمة إعداد.
        إذا لم يكن موجودًا → يرجع القيمة الافتراضية.
        """

        conn = self.connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT value FROM settings
            WHERE key = ?
        """, (key,))

        row = cur.fetchone()
        conn.close()

        return row[0] if row else default

    # ----------------------------------------------------------
    # FREE TRIAL SETTINGS
    # ----------------------------------------------------------

    def enable_free_trial(self):
        """
        تفعيل التجربة المجانية.
        """
        self.set_setting("free_trial_enabled", "1")

    def disable_free_trial(self):
        """
        إيقاف التجربة المجانية.
        """
        self.set_setting("free_trial_enabled", "0")

    def is_free_trial_enabled(self):
        """
        التحقق من أن التجربة المجانية مفعّلة.
        """
        return self.get_setting("free_trial_enabled", "0") == "1"

    # ----------------------------------------------------------

    def set_free_trial_days(self, days):
        """
        تحديد مدة التجربة المجانية.
        """
        self.set_setting("free_trial_days", str(days))

    def get_free_trial_days(self):
        """
        جلب مدة التجربة المجانية.
        """
        return int(self.get_setting("free_trial_days", "0"))

    # ==========================================================
    # PHASE 7 — USER MANAGEMENT (ACCESS LAYER)
    # ==========================================================

    def get_users_list(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, first_name
            FROM users
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_user_details(self, user_id):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, tg_id, first_name, username, join_date, last_activity, subscription_status
            FROM users
            WHERE id = ?
        """, (user_id,))
        row = cur.fetchone()
        conn.close()
        return row

    def find_user(self, query):
        conn = self.connect()
        cur = conn.cursor()

        try:
            as_int = int(query)
        except ValueError:
            as_int = None

        if as_int is not None:
            cur.execute("""
                SELECT id, first_name, username, subscription_status
                FROM users
                WHERE id = ? OR tg_id = ?
            """, (as_int, as_int))
        else:
            cur.execute("""
                SELECT id, first_name, username, subscription_status
                FROM users
                WHERE username = ?
            """, (query,))

        row = cur.fetchone()
        conn.close()
        return row

    def get_user_role(self, tg_id):
        """
        جلب دور المستخدم الحقيقي بناءً على Telegram ID.
        لأن TelegramApp يمرّر user.id وهو tg_id وليس user_id داخل قاعدة البيانات.
        """
        return self.get_setting(f"user_role_{tg_id}", "user")


    # ==========================================================
    # PHASE 8 — ADMIN ACCESS LAYER (NO SQL IN BotInterface)
    # ==========================================================

    def get_active_subscribers(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.first_name, s.end_date
            FROM subscriptions s
            JOIN users u ON u.id = s.user_id
            WHERE s.status = 'active'
            ORDER BY s.id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_expired_subscriptions(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT u.id, u.first_name, s.end_date
            FROM subscriptions s
            JOIN users u ON u.id = s.user_id
            WHERE s.status = 'expired'
            ORDER BY s.id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_subscription_logs(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, user_id, action, date, details
            FROM subscription_logs
            ORDER BY id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_manual_subscription_requests(self):
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT r.id, u.first_name, r.plan_id, r.request_date, r.status
            FROM subscription_requests r
            JOIN users u ON u.id = r.user_id
            WHERE r.status = 'pending'
            ORDER BY r.id DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_subscription_mode(self):
        return self.get_setting("subscription_mode", "manual")

    def set_subscription_mode(self, mode):
        self.set_setting("subscription_mode", mode)

    def get_user_subscription(self, user_id):
        """
        دالة ذكية لعرض حالة اشتراك المستخدم في صفحة الاشتراك.
        ترجع:
        - active
        - expired
        - none
        """
        active = self.get_active_subscription(user_id)
        if active:
            return {
                "status": "active",
                "plan_id": active["plan_id"],
                "start_date": active["start_date"],
                "end_date": active["end_date"]
            }

        # إذا لا يوجد اشتراك نشط، نبحث عن آخر اشتراك منتهي
        conn = self.connect()
        cur = conn.cursor()
        cur.execute("""
            SELECT plan_id, start_date, end_date
            FROM subscriptions
            WHERE user_id = ? AND status = 'expired'
            ORDER BY id DESC
            LIMIT 1
        """, (user_id,))
        row = cur.fetchone()
        conn.close()

        if row:
            return {
                "status": "expired",
                "plan_id": row[0],
                "start_date": row[1],
                "end_date": row[2]
            }

        return {"status": "none"}

    def get_free_trial_settings(self):
        return {
            "enabled": self.is_free_trial_enabled(),
            "days": self.get_free_trial_days()
        }

