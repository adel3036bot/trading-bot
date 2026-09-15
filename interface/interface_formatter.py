# ==========================================================
# ADEL SMART BOT ELITE
# Interface Formatter (LOCKED — Final Version)
# ==========================================================

class InterfaceFormatter:
    """
    مسؤول عن:
    - تنسيق جميع الرسائل النصية.
    - بناء رسالة الترحيب.
    - بناء رسائل القوائم.
    - بناء بطاقات الأخبار والتقارير والتحليلات.
    - بناء رسائل لوحة الإدارة.
    - بناء رسائل النظام.
    - رسائل الاشتراكات.

    هذا الملف مسؤول عن تنسيق المحتوى فقط.
    """

    # ==========================================================
    # PLAN CONSTANTS
    # ==========================================================

    PLAN_BIWEEKLY = 1
    PLAN_MONTHLY = 2
    PLAN_YEARLY = 3

    # ==========================================================
    # INITIALIZATION
    # ==========================================================

    def __init__(self, channel_url: str):
        self.channel_url = channel_url
        self.bot_name = "ADEL SMART BOT ELITE"

    # ==========================================================
    # INTERNAL — PLAN NAME RESOLVER
    # ==========================================================

    def _get_plan_name(self, plan_id: int) -> str:
        if plan_id == self.PLAN_BIWEEKLY:
            return "أسبوعين"
        elif plan_id == self.PLAN_MONTHLY:
            return "شهري"
        elif plan_id == self.PLAN_YEARLY:
            return "سنوي"
        return "غير معروف"

    # ==========================================================
    # WELCOME MESSAGE
    # ==========================================================

    def build_welcome_message(self, first_name: str) -> str:
        return f"""👋 أهلاً بك، {first_name}!

مرحبًا بك في

🤖 {self.bot_name}

━━━━━━━━━━━━━━━━━━

منصة ذكية لتحليل السوق الأمريكي باستخدام الذكاء الاصطناعي وخوارزميات تحليل خاصة بـ ADEL SMART BOT، لتقديم تحليلات احترافية لعقود الخيارات (CALL / PUT)، والأسهم، والمؤشرات، والأخبار الاقتصادية المؤثرة، بما يساعدك على اتخاذ قرارات تداول أكثر وعيًا.

━━━━━━━━━━━━━━━━━━

🔥 لا تفوت أهم فرص السوق

انضم إلى القناة الرسمية لـ ADEL SMART BOT واستفد من منظومة متكاملة تشمل:

🎯 أفضل عقود الخيارات والفرص التي اجتازت نظام الفلترة الذكي.
📊 التحليل اليومي قبل افتتاح السوق الأمريكي.
🚨 الأخبار الاقتصادية وأخبار الشركات المؤثرة.
📈 تحديثات الصفقات والأهداف أثناء جلسة التداول.
📑 تقارير الأداء والإحصائيات.
⭐ الميزات الجديدة والتحديثات قبل الجميع.

━━━━━━━━━━━━━━━━━━

📢 القناة الرسمية
{self.channel_url}

━━━━━━━━━━━━━━━━━━

⚠️ إخلاء مسؤولية
جميع المعلومات والتحليلات المعروضة داخل ADEL SMART BOT هي لأغراض تعليمية ومعلوماتية فقط، ولا تُعد توصية مباشرة بالبيع أو الشراء.

يبقى قرار الاستثمار والتداول مسؤولية المستخدم بالكامل.

━━━━━━━━━━━━━━━━━━

🎯 لا نبحث عن أكبر عدد من الفرص...
بل نبحث عن الفرص التي تستحق المتابعة.
"""

    # ==========================================================
    # HOME PAGE
    # ==========================================================

    def build_home_message(self) -> str:
        return f"""🏠 الصفحة الرئيسية

مرحبًا بك في {self.bot_name}

اختر القسم الذي ترغب في استعراضه من القائمة الموجودة أسفل هذه الرسالة.

━━━━━━━━━━━━━━━━━━

📈 السوق
🎯 الفرص
📰 الأخبار
📊 التقارير
🖼 التحليلات
📢 القناة الرسمية
⚙️ الإعدادات
❓ المساعدة

━━━━━━━━━━━━━━━━━━

🎯 اختر أحد الأقسام من الأزرار بالأسفل.
"""

    # ==========================================================
    # SMART CARDS
    # ==========================================================

    def _build_smart_card(self, title: str, description: str, footer: str = "") -> str:
        message = f"""{title}

━━━━━━━━━━━━━━━━━━

{description}
"""
        if footer:
            message += f"""

━━━━━━━━━━━━━━━━━━

{footer}
"""
        return message.strip()

    def build_pre_market_card(self) -> str:
        return self._build_smart_card(
            "🌅 تقرير ما قبل الافتتاح",
            "جاري تجهيز التقرير الصباحي للسوق الأمريكي.\n\nسيتم عرض صورة التقرير الاحترافية مع الملخص النصي."
        )

    def build_market_card(self) -> str:
        return self._build_smart_card(
            "🎯 أفضل فرصة حالية",
            "جاري تجهيز أفضل فرصة اجتازت نظام الفلترة الذكي.\n\nسيتم عرض الصورة الاحترافية مع الملخص النصي."
        )

    def build_breaking_news_card(self) -> str:
        return self._build_smart_card(
            "🚨 خبر عاجل",
            "تم رصد خبر مؤثر على السوق.\n\nسيتم عرض الصورة الاحترافية مع ملخص الخبر وتأثيره."
        )

    def build_after_market_card(self) -> str:
        return self._build_smart_card(
            "🌙 تقرير إغلاق السوق",
            "جاري تجهيز تقرير نهاية الجلسة.\n\nسيتم عرض الصورة الاحترافية مع ملخص الأداء."
        )

    # ==========================================================
    # MENU MESSAGES
    # ==========================================================

    def _build_menu_message(self, title: str, description: str, note: str = "") -> str:
        message = f"""{title}

━━━━━━━━━━━━━━━━━━

{description}
"""
        if note:
            message += f"""

━━━━━━━━━━━━━━━━━━

{note}
"""
        return message.strip()

    def build_market_message(self) -> str:
        return self._build_menu_message(
            "📈 السوق",
            "اختر القسم الذي ترغب باستعراضه:\n\n• المؤشرات\n• الذهب\n• البيتكوين\n• التقويم الاقتصادي",
            "📊 جميع التحليلات تعرض بصورة احترافية مع ملخص نصي."
        )

    def build_opportunities_message(self) -> str:
        return self._build_menu_message(
            "🎯 الفرص",
            "يعرض هذا القسم الصفقات المكتملة التي حققت أهدافها.\n\nأما الفرص الجديدة فتُنشر داخل القناة الرسمية.",
            "📢 اضغط على زر القناة الرسمية للحصول على الفرص الكاملة."
        )

    def build_news_message(self) -> str:
        return self._build_menu_message(
            "📰 الأخبار",
            "استعرض أهم الأخبار الاقتصادية وأخبار الشركات المؤثرة على السوق.",
            "🖼 جميع الأخبار تعرض بصورة احترافية مع ملخص نصي."
        )

    def build_reports_message(self) -> str:
        return self._build_menu_message(
            "📊 التقارير",
            "تقارير احترافية للسوق الأمريكي قبل الافتتاح وأثناء التداول وبعد الإغلاق.",
            "📑 جميع التقارير تعرض بصورة احترافية مع ملخص نصي."
        )

    def build_analysis_message(self) -> str:
        return self._build_menu_message(
            "🖼 التحليلات",
            "تحليلات احترافية للمؤشرات الرئيسية وحركة السوق.",
            "📈 تعتمد جميع التحليلات على صور احترافية مع شرح مختصر."
        )

    def build_settings_message(self) -> str:
        return self._build_menu_message(
            "⚙️ الإعدادات",
            "يمكنك إدارة إعدادات البوت والإشعارات واللغة من هذه القائمة."
        )

    def build_help_message(self) -> str:
        return self._build_menu_message(
            "❓ المساعدة",
            "ستجد هنا دليل الاستخدام والأسئلة الشائعة وطرق الاستفادة من المنصة."
        )

    # ==========================================================
    # CHANNEL MESSAGE
    # ==========================================================

    def build_channel_message(self) -> str:
        return f"""📢 القناة الرسمية

━━━━━━━━━━━━━━━━━━

انضم إلى القناة الرسمية لـ {self.bot_name} للحصول على:

🎯 الفرص الجديدة لحظة صدورها.
📈 تحديثات الصفقات المباشرة.
📰 أهم الأخبار المؤثرة.
📊 التقارير اليومية.
🖼 التحليلات الاحترافية.

━━━━━━━━━━━━━━━━━━

{self.channel_url}
"""

    # ==========================================================
    # ADMIN PANEL — USERS LIST
    # ==========================================================

    def build_admin_users_list_message(self, users: list) -> str:
        if not users:
            return "📋 قائمة المستخدمين\n\nلا يوجد مستخدمين حتى الآن.\n\n⬅️ رجوع"

        lines = ["📋 قائمة المستخدمين\n━━━━━━━━━━━━━━━━━━\n\n"]

        for index, user in enumerate(users, start=1):
            name = user.get("name") or "User"
            user_id = user.get("id")
            lines.append(f"{index}. 👤 {name} — المستخدم رقم {user_id}\n")

        lines.append("\n⬅️ رجوع")
        return "".join(lines)

    # ==========================================================
    # ADMIN PANEL — USER DETAILS
    # ==========================================================

    def build_admin_user_details_message(self, user_row) -> str:
        """
        user_row يأتي من DatabaseManager.get_user_details:
        (id, tg_id, first_name, username, join_date, last_activity, subscription_status)
        """
        user_id = user_row[0]
        tg_id = user_row[1]
        first_name = user_row[2] or "User"
        username = user_row[3]
        join_date = user_row[4]
        last_activity = user_row[5]
        status = user_row[6]

        if status == "active":
            status_icon = "🟢 مشترك"
        elif status == "expired":
            status_icon = "🟡 منتهي الاشتراك"
        else:
            status_icon = "🔴 غير مشترك"

        username_display = f"@{username}" if username else "غير متوفر"

        return f"""👤 معلومات المستخدم
━━━━━━━━━━━━━━━━━━

🆔 الرقم الداخلي:
{user_id}

🆔 Telegram ID:
{tg_id}

👤 الاسم:
{first_name}

🔗 Username:
{username_display}

📅 تاريخ الانضمام:
{join_date}

⏱ آخر نشاط:
{last_activity}

⭐ حالة الاشتراك:
{status_icon}

━━━━━━━━━━━━━━━━━━

⬅️ رجوع
"""

    # ==========================================================
    # SYSTEM MESSAGES
    # ==========================================================

    def build_loading_message(self) -> str:
        return "⏳ جاري تجهيز المحتوى..."

    def build_error_message(self) -> str:
        return "❌ حدث خطأ أثناء تنفيذ الطلب.\n\nيرجى المحاولة مرة أخرى بعد قليل."

    def build_success_message(self, message: str) -> str:
        return f"✅ {message}"

    def build_not_available_message(self) -> str:
        return "ℹ️ لا يوجد محتوى متاح حاليًا.\n\nيرجى المحاولة لاحقًا."

    def build_under_development_message(self) -> str:
        return (
            "🚧 هذا القسم قيد التطوير.\n\n"
            "نعمل حاليًا على تجهيز هذا المحتوى.\n"
            "يمكنك اختيار عنصر آخر من نفس القائمة."
        )

    # ==========================================================
    # SUBSCRIPTIONS — USER SIDE (NEW PHILOSOPHY)
    # ==========================================================

    def build_subscription_plans_message(self) -> str:
        return """💳 اختر مدة الاشتراك

🗓️ أسبوعين
🗓️ شهري
🗓️ سنوي (قريبًا)
"""

    def build_subscription_status_message(self, subscription: dict) -> str:
        plan_name = self._get_plan_name(subscription.get("plan_id"))
        start_date = subscription.get("start_date")
        end_date = subscription.get("end_date")

        return f"""💳 حالة الاشتراك

━━━━━━━━━━━━━━━━━━

🟢 اشتراكك نشط

📅 تاريخ البداية:
{start_date}

📅 تاريخ الانتهاء:
{end_date}

⭐ مدة الاشتراك:
{plan_name}

━━━━━━━━━━━━━━━━━━

يمكنك تجديد الاشتراك أو إعادة إرسال رابط الدعوة.
"""

    def build_subscription_expired_message(self, subscription: dict) -> str:
        plan_name = self._get_plan_name(subscription.get("plan_id"))
        end_date = subscription.get("end_date")

        return f"""⏳ الاشتراك منتهي

━━━━━━━━━━━━━━━━━━

📅 تاريخ الانتهاء:
{end_date}

⭐ مدة الاشتراك السابقة:
{plan_name}

━━━━━━━━━━━━━━━━━━

يمكنك التجديد أو الاشتراك من جديد عبر متجر سلة.
"""

    def build_subscription_renew_placeholder_message(self) -> str:
        return """🔄 تجديد الاشتراك

━━━━━━━━━━━━━━━━━━

سيتم إضافة نظام التجديد قريبًا.
"""

    def build_subscription_resend_invite_placeholder_message(self) -> str:
        return """🔗 إعادة إرسال رابط الدعوة

━━━━━━━━━━━━━━━━━━

سيتم إضافة هذه الميزة قريبًا.
"""

    def build_subscription_store_message(self) -> str:
        return """🛒 متجر سلة

━━━━━━━━━━━━━━━━━━

سيتم توجيهك إلى متجر سلة لإتمام الاشتراك.
"""

    # ==========================================================
    # ADMIN — SUBSCRIPTIONS PANEL
    # ==========================================================

    def build_admin_subscriptions_menu_message(self) -> str:
        return """💳 إدارة الاشتراكات

━━━━━━━━━━━━━━━━━━

👥 المشتركون
⏳ المنتهية
📄 سجل العمليات
🎁 التجربة المجانية
⚙️ إعدادات الاشتراك
🆕 طلبات الاشتراك

━━━━━━━━━━━━━━━━━━

اختر من القائمة بالأسفل.
"""

    def build_admin_subscribers_message(self, rows) -> str:
        if not rows:
            return """🟢 المشتركون النشطون

━━━━━━━━━━━━━━━━━━

لا يوجد مشتركون نشطون.
"""
        lines = ["🟢 المشتركون النشطون\n━━━━━━━━━━━━━━━━━━\n\n"]
        for r in rows:
            first_name = r[1] or "User"
            end_date = r[2]
            lines.append(f"• {first_name} — ينتهي في {end_date}\n")
        return "".join(lines)

    def build_admin_expired_subscriptions_message(self, rows) -> str:
        if not rows:
            return """⏳ الاشتراكات المنتهية

━━━━━━━━━━━━━━━━━━

لا يوجد اشتراكات منتهية.
"""
        lines = ["⏳ الاشتراكات المنتهية\n━━━━━━━━━━━━━━━━━━\n\n"]
        for r in rows:
            first_name = r[1] or "User"
            end_date = r[2]
            lines.append(f"• {first_name} — انتهى في {end_date}\n")
        return "".join(lines)

    def build_admin_subscription_logs_message(self, rows) -> str:
        if not rows:
            return """📄 سجل العمليات

━━━━━━━━━━━━━━━━━━

لا يوجد سجل عمليات.
"""
        lines = ["📄 سجل العمليات\n━━━━━━━━━━━━━━━━━━\n\n"]
        for r in rows:
            action = r[2]
            date = r[3]
            details = r[4] or ""
            lines.append(f"• {action} — {date}\n")
            if details:
                lines.append(f"  📌 {details}\n")
        return "".join(lines)

    def build_admin_free_trial_message(self, settings) -> str:
        days = settings.get("days", 0)
        enabled = settings.get("enabled", False)

        return f"""🎁 التجربة المجانية

━━━━━━━━━━━━━━━━━━

📅 المدة:
{days} يوم

⭐ الحالة:
{"مفعلة" if enabled else "معطلة"}

━━━━━━━━━━━━━━━━━━
"""

    def build_admin_subscription_settings_message(self, mode: str) -> str:
        return f"""⚙️ إعدادات الاشتراك

━━━━━━━━━━━━━━━━━━

الوضع الحالي:
{"آلي" if mode == "auto" else "يدوي"}

━━━━━━━━━━━━━━━━━━
"""

    def build_admin_subscription_requests_message(self, rows) -> str:
        if not rows:
            return """🆕 طلبات الاشتراك

━━━━━━━━━━━━━━━━━━

لا توجد طلبات اشتراك.
"""
        lines = ["🆕 طلبات الاشتراك\n━━━━━━━━━━━━━━━━━━\n\n"]
        for r in rows:
            req_id = r[0]
            first_name = r[1] or "User"
            plan_name = self._get_plan_name(r[2])
            request_date = r[3]
            status = r[4]

            lines.append(
                f"• الطلب رقم: {req_id}\n"
                f"  👤 الاسم: {first_name}\n"
                f"  ⭐ مدة الاشتراك: {plan_name}\n"
                f"  📅 التاريخ: {request_date}\n"
                f"  🔖 الحالة: {status}\n\n"
            )
        return "".join(lines)
