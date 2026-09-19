# ==========================================================
# ADEL SMART BOT ELITE
# Database Manager — Phase 1 (Final 10/10)
# ==========================================================

import json
import sqlite3
import hashlib
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from core.signal_schema import AssetClass, Direction, InstrumentType, Signal, build_signal_id


class DatabaseManager:
    """
    المرحلة الأولى:
    - إنشاء الجداول الأساسية
    - تفعيل القيود المرجعية
    - إضافة NOT NULL للأعمدة الأساسية
    - إضافة قيم افتراضية للحالات
    - إضافة فهارس لتحسين الأداء
    """

    def __init__(self, db_path=None):
        # Resolve the production journal once from this module, rather than
        # from whichever working directory launched a scheduler/test process.
        # Explicit test or deployment paths remain supported unchanged.
        self.db_path = str(
            Path(db_path) if db_path is not None else Path(__file__).resolve().parents[1] / "adel_smart_bot.db"
        )
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

        # ----------------------------------------------------------
        # SIGNAL JOURNAL — additive only; existing subscriber tables
        # are intentionally never altered or rebuilt.
        # ----------------------------------------------------------
        cur.execute("""
            CREATE TABLE IF NOT EXISTS signal_journal (
                signal_id TEXT PRIMARY KEY,
                asset_class TEXT NOT NULL,
                instrument_type TEXT,
                symbol TEXT NOT NULL,
                contract_symbol TEXT,
                direction TEXT,
                strategy TEXT,
                entry REAL,
                stop_loss REAL,
                targets_json TEXT,
                entry_timeframe TEXT,
                source_timestamp TEXT,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                data_quality TEXT,
                rejection_reason TEXT,
                metadata_json TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS trade_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL,
                opened_at TEXT NOT NULL,
                last_event_at TEXT,
                state_json TEXT,
                last_price_timestamp TEXT,
                closed_at TEXT,
                metadata_json TEXT,
                FOREIGN KEY(signal_id) REFERENCES signal_journal(signal_id)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS signal_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT NOT NULL,
                trade_id INTEGER,
                event_type TEXT NOT NULL,
                event_key TEXT,
                event_timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                metadata_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(signal_id) REFERENCES signal_journal(signal_id),
                FOREIGN KEY(trade_id) REFERENCES trade_journal(id)
            )
        """)

        # Upgrade existing Phase 5 databases without rebuilding any table.
        self._ensure_columns(cur, "trade_journal", {
            "state_json": "TEXT",
            "last_price_timestamp": "TEXT",
            "closed_at": "TEXT",
        })
        self._ensure_columns(cur, "signal_events", {"event_key": "TEXT"})

        cur.execute("""
            CREATE TABLE IF NOT EXISTS signal_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                signal_id TEXT NOT NULL,
                event_id INTEGER,
                destination TEXT NOT NULL,
                delivery_kind TEXT NOT NULL,
                attempted_at TEXT NOT NULL,
                success INTEGER NOT NULL,
                failure_reason TEXT,
                metadata_json TEXT,
                FOREIGN KEY(signal_id) REFERENCES signal_journal(signal_id),
                FOREIGN KEY(event_id) REFERENCES signal_events(id)
            )
        """)

        cur.execute("CREATE INDEX IF NOT EXISTS idx_signal_journal_identity ON signal_journal(asset_class, symbol, contract_symbol);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_trade_journal_signal_id ON trade_journal(signal_id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_signal_events_signal_id ON signal_events(signal_id, event_timestamp);")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_signal_events_dedup ON signal_events(signal_id, event_key) WHERE event_key IS NOT NULL;")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_signal_deliveries_signal_id ON signal_deliveries(signal_id, attempted_at);")

        # NEWS JOURNAL — separate from signals: news is context, not a trade.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS news_journal (
                news_id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                source_url TEXT,
                source_timestamp TEXT,
                title TEXT,
                status TEXT NOT NULL,
                metadata_json TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS news_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id TEXT NOT NULL,
                destination TEXT NOT NULL,
                attempted_at TEXT NOT NULL,
                success INTEGER NOT NULL,
                failure_reason TEXT,
                metadata_json TEXT,
                FOREIGN KEY(news_id) REFERENCES news_journal(news_id)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_news_journal_status ON news_journal(status, source_timestamp);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_news_deliveries_news_id ON news_deliveries(news_id, attempted_at);")
        # Translation is persisted separately from delivery status.  A news
        # record may become SENT after a successful translation, so status
        # alone cannot safely serve as the translation cache key.
        self._ensure_columns(cur, "news_journal", {
            "translated_title": "TEXT",
            "translated_summary": "TEXT",
            "translation_metadata_json": "TEXT",
        })
        cur.execute("""CREATE TABLE IF NOT EXISTS report_journal (
            report_key TEXT PRIMARY KEY, report_type TEXT NOT NULL, period_start TEXT NOT NULL,
            period_end TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, metadata_json TEXT)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS report_deliveries (
            id INTEGER PRIMARY KEY AUTOINCREMENT, report_key TEXT NOT NULL, destination TEXT NOT NULL,
            attempted_at TEXT NOT NULL, success INTEGER NOT NULL, failure_reason TEXT, metadata_json TEXT)""")

        conn.commit()
        conn.close()

    @staticmethod
    def _ensure_columns(cur, table, columns):
        existing = {row[1] for row in cur.execute(f"PRAGMA table_info({table})")}
        for name, definition in columns.items():
            if name not in existing:
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")

    # ==========================================================
    # SIGNAL JOURNAL — persistence only, never strategy/risk logic
    # ==========================================================

    @staticmethod
    def _redact_secrets(value):
        if isinstance(value, Mapping):
            redacted = {}
            for key, item in value.items():
                key_text = str(key).lower()
                if any(marker in key_text for marker in ("token", "api_key", "apikey", "secret", "password")):
                    redacted[str(key)] = "[REDACTED]"
                else:
                    redacted[str(key)] = DatabaseManager._redact_secrets(item)
            return redacted
        if isinstance(value, (list, tuple, set)):
            return [DatabaseManager._redact_secrets(item) for item in value]
        return value

    @staticmethod
    def _json(value):
        return json.dumps(DatabaseManager._redact_secrets(value), ensure_ascii=False, default=str, separators=(",", ":"))

    @staticmethod
    def _value(payload, key, default=None):
        if isinstance(payload, Signal):
            return getattr(payload, key, default)
        return payload.get(key, default)

    def _journal_signal(self, payload: Signal | Mapping[str, object]):
        """Extract supplied values for persistence without calculating a setup."""
        if not isinstance(payload, (Signal, Mapping)):
            raise TypeError("signal_payload_must_be_signal_or_mapping")

        if isinstance(payload, Signal):
            return {
                "signal_id": payload.signal_id,
                "asset_class": payload.asset_class.value,
                "instrument_type": payload.instrument_type.value,
                "symbol": payload.symbol,
                "contract_symbol": payload.metadata.get("contract_symbol"),
                "direction": payload.direction.value,
                "strategy": payload.setup,
                "entry": payload.entry,
                "stop_loss": payload.stop_loss,
                "targets": [payload.tp1, payload.tp2, payload.tp3],
                "entry_timeframe": payload.entry_timeframe,
                "source_timestamp": payload.source_timestamp.isoformat(),
                "created_at": payload.signal_timestamp.isoformat(),
                "status": "NEW",
                "data_quality": payload.data_quality.value,
                "rejection_reason": None,
                "metadata": dict(payload.metadata),
            }

        direction_value = str(payload.get("direction") or payload.get("signal_type") or "").upper()
        direction = next((item.value for item in Direction if item.value in direction_value), None)
        asset_value = payload.get("asset_class")
        if asset_value is None and direction in (Direction.CALL.value, Direction.PUT.value) and payload.get("contract_symbol"):
            asset_value = AssetClass.OPTIONS.value
        try:
            asset_class = AssetClass(str(asset_value).upper())
        except ValueError as error:
            raise ValueError("journal_asset_class_required") from error
        if direction is None:
            raise ValueError("journal_direction_required")

        instrument_value = payload.get("instrument_type")
        if instrument_value is None:
            instrument_value = InstrumentType.OPTION.value if asset_class is AssetClass.OPTIONS else InstrumentType.EQUITY.value
        try:
            instrument_type = InstrumentType(str(instrument_value).upper())
        except ValueError as error:
            raise ValueError("journal_instrument_type_invalid") from error

        symbol = str(payload.get("symbol") or "").strip().upper()
        if not symbol:
            raise ValueError("journal_symbol_required")
        strategy = str(payload.get("strategy") or payload.get("setup") or payload.get("approval") or f"LEGACY_{asset_class.value}")
        timestamp_value = payload.get("signal_timestamp") or payload.get("created_at") or self.now().isoformat()
        try:
            signal_timestamp = datetime.fromisoformat(str(timestamp_value))
        except ValueError:
            signal_timestamp = self.now()
        if signal_timestamp.tzinfo is None:
            signal_timestamp = signal_timestamp.replace(tzinfo=self.now().tzinfo)

        supplied_signal_id = payload.get("signal_id")
        signal_id = str(supplied_signal_id) if supplied_signal_id else build_signal_id(
            asset_class=asset_class,
            instrument_type=instrument_type,
            symbol=symbol,
            direction=Direction(direction),
            setup=strategy,
            signal_timestamp=signal_timestamp.astimezone(timezone.utc),
        )
        targets = payload.get("targets") or [payload.get("tp1"), payload.get("tp2"), payload.get("tp3")]
        return {
            "signal_id": signal_id,
            "asset_class": asset_class.value,
            "instrument_type": instrument_type.value,
            "symbol": symbol,
            "contract_symbol": payload.get("contract_symbol"),
            "direction": direction,
            "strategy": strategy,
            "entry": payload.get("entry", payload.get("entry_price")),
            "stop_loss": payload.get("stop_loss", payload.get("sl", payload.get("stop"))),
            "targets": targets,
            "entry_timeframe": payload.get("entry_timeframe"),
            "source_timestamp": payload.get("source_timestamp"),
            "created_at": signal_timestamp.isoformat(),
            "status": payload.get("status", "NEW"),
            "data_quality": payload.get("data_quality"),
            "rejection_reason": payload.get("rejection_reason"),
            "metadata": payload.get("metadata", {}),
        }

    def record_signal(self, payload: Signal | Mapping[str, object]) -> tuple[str, bool]:
        """Persist one ready signal and return (signal_id, inserted)."""
        signal = self._journal_signal(payload)
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO signal_journal (
                    signal_id, asset_class, instrument_type, symbol, contract_symbol,
                    direction, strategy, entry, stop_loss, targets_json, entry_timeframe,
                    source_timestamp, created_at, status, data_quality, rejection_reason,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(signal_id) DO NOTHING
            """, (
                signal["signal_id"], signal["asset_class"], signal["instrument_type"], signal["symbol"], signal["contract_symbol"],
                signal["direction"], signal["strategy"], signal["entry"], signal["stop_loss"], self._json(signal["targets"]),
                signal["entry_timeframe"], signal["source_timestamp"], signal["created_at"], signal["status"], signal["data_quality"],
                signal["rejection_reason"], self._json(signal["metadata"]),
            ))
            inserted = cur.rowcount == 1
            cur.execute("""
                INSERT INTO trade_journal (signal_id, status, opened_at, metadata_json)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(signal_id) DO NOTHING
            """, (signal["signal_id"], signal["status"], signal["created_at"], self._json({})))
            conn.commit()
            return signal["signal_id"], inserted
        finally:
            conn.close()

    def record_event(self, signal_id: str, event_type: str, *, event_timestamp=None, status="RECORDED", metadata=None):
        """Append an event linked to its original signal/trade; no lifecycle logic."""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM trade_journal WHERE signal_id = ?", (signal_id,))
            row = cur.fetchone()
            if row is None:
                raise ValueError("journal_signal_not_found")
            timestamp = event_timestamp or self.now().isoformat()
            cur.execute("""
                INSERT INTO signal_events (signal_id, trade_id, event_type, event_timestamp, status, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (signal_id, row[0], str(event_type), str(timestamp), status, self._json(metadata or {}), self.now().isoformat()))
            event_id = cur.lastrowid
            cur.execute("UPDATE trade_journal SET last_event_at = ? WHERE id = ?", (str(timestamp), row[0]))
            conn.commit()
            return event_id
        finally:
            conn.close()

    def record_event_once(self, signal_id: str, event_type: str, event_key: str, *, event_timestamp=None, status="RECORDED", metadata=None):
        """Persist an event once across restarts and return (event_id, inserted)."""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id FROM trade_journal WHERE signal_id = ?", (signal_id,))
            row = cur.fetchone()
            if row is None:
                raise ValueError("journal_signal_not_found")
            timestamp = event_timestamp or self.now().isoformat()
            cur.execute("""
                INSERT OR IGNORE INTO signal_events (
                    signal_id, trade_id, event_type, event_key, event_timestamp,
                    status, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_id, row[0], str(event_type), event_key, str(timestamp), status,
                self._json(metadata or {}), self.now().isoformat(),
            ))
            inserted = cur.rowcount == 1
            if inserted:
                event_id = cur.lastrowid
                cur.execute("UPDATE trade_journal SET last_event_at = ? WHERE id = ?", (str(timestamp), row[0]))
            else:
                event_id = cur.execute(
                    "SELECT id FROM signal_events WHERE signal_id = ? AND event_key = ?",
                    (signal_id, event_key),
                ).fetchone()[0]
            conn.commit()
            return event_id, inserted
        finally:
            conn.close()

    def persist_trade_state(self, signal_id: str, trade: Mapping[str, object], *, price_timestamp=None, status=None, closed=False):
        """Persist ready trade state atomically; it never calculates trade values."""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM trade_journal WHERE signal_id = ?", (signal_id,))
            if cur.fetchone() is None:
                raise ValueError("journal_signal_not_found")
            journal_status = status or str(trade.get("status") or "ACTIVE")
            closed_at = self.now().isoformat() if closed else None
            cur.execute("""
                UPDATE trade_journal
                SET status = ?, state_json = ?, last_price_timestamp = ?, closed_at = COALESCE(?, closed_at)
                WHERE signal_id = ?
            """, (
                journal_status,
                self._json(dict(trade)),
                str(price_timestamp) if price_timestamp else None,
                closed_at,
                signal_id,
            ))
            conn.commit()
        finally:
            conn.close()

    def get_trade_state(self, signal_id: str):
        conn = self.connect()
        try:
            row = conn.execute(
                "SELECT state_json, status, last_price_timestamp, closed_at FROM trade_journal WHERE signal_id = ?",
                (signal_id,),
            ).fetchone()
            if row is None or not row[0]:
                return None
            state = json.loads(row[0])
            state.setdefault("status", row[1])
            state.setdefault("last_price_timestamp", row[2])
            state.setdefault("closed_at", row[3])
            return state
        finally:
            conn.close()

    def get_active_trade_states(self):
        conn = self.connect()
        try:
            rows = conn.execute("""
                SELECT signal_id, state_json, status, last_price_timestamp
                FROM trade_journal
                WHERE state_json IS NOT NULL AND closed_at IS NULL
                ORDER BY id ASC
            """).fetchall()
            states = []
            for signal_id, state_json, status, price_timestamp in rows:
                state = json.loads(state_json)
                state.setdefault("signal_id", signal_id)
                state.setdefault("status", status)
                state.setdefault("last_price_timestamp", price_timestamp)
                states.append(state)
            return states
        finally:
            conn.close()

    def record_delivery(self, signal_id: str, destination, *, event_id=None, delivery_kind="TELEGRAM", success=False, failure_reason=None, metadata=None):
        """Append a delivery attempt without storing credentials or message secrets."""
        conn = self.connect()
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1 FROM signal_journal WHERE signal_id = ?", (signal_id,))
            if cur.fetchone() is None:
                raise ValueError("journal_signal_not_found")
            cur.execute("""
                INSERT INTO signal_deliveries (
                    signal_id, event_id, destination, delivery_kind, attempted_at,
                    success, failure_reason, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_id, event_id, str(destination), delivery_kind, self.now().isoformat(), int(bool(success)),
                failure_reason, self._json(metadata or {}),
            ))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    # ==========================================================
    # NEWS JOURNAL — persistence/delivery only, never news scoring
    # ==========================================================

    @staticmethod
    def build_news_id(news: Mapping[str, object]) -> str:
        """Stable identity prefers provider URL, never the title alone."""
        source = str(news.get("source") or "").strip().lower()
        url = str(news.get("url") or "").strip()
        published = str(news.get("timestamp") or news.get("published") or "").strip()
        title = str(news.get("headline") or news.get("title") or "").strip().lower()
        return hashlib.sha256("|".join((source, url or title, published)).encode("utf-8")).hexdigest()

    def record_news(self, news: Mapping[str, object], *, status="FETCHED", metadata=None) -> str:
        if not isinstance(news, Mapping):
            raise TypeError("news_payload_must_be_mapping")
        news_id = self.build_news_id(news)
        source = str(news.get("source") or "").strip()
        if not source:
            raise ValueError("news_source_required")
        now = self.now().isoformat()
        conn = self.connect()
        try:
            conn.execute("""
                INSERT INTO news_journal (news_id, source, source_url, source_timestamp, title, status, metadata_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(news_id) DO UPDATE SET
                    status = CASE WHEN news_journal.status = 'SENT' THEN 'SENT' ELSE excluded.status END,
                    metadata_json = excluded.metadata_json,
                    updated_at = excluded.updated_at
            """, (news_id, source, str(news.get("url") or "") or None,
                  str(news.get("timestamp") or news.get("published") or "") or None,
                  str(news.get("headline") or news.get("title") or "") or None,
                  str(status), self._json(metadata or {}), now, now))
            conn.commit()
            return news_id
        finally:
            conn.close()

    def news_was_sent(self, news_id: str) -> bool:
        conn = self.connect()
        try:
            row = conn.execute("SELECT status FROM news_journal WHERE news_id = ?", (news_id,)).fetchone()
            return bool(row and row[0] == "SENT")
        finally:
            conn.close()

    def update_news_status(self, news_id: str, status: str, *, metadata=None) -> None:
        conn = self.connect()
        try:
            cur = conn.execute("UPDATE news_journal SET status = ?, metadata_json = ?, updated_at = ? WHERE news_id = ?",
                               (str(status), self._json(metadata or {}), self.now().isoformat(), news_id))
            if cur.rowcount != 1:
                raise ValueError("news_journal_not_found")
            conn.commit()
        finally:
            conn.close()

    def get_news_translation(self, news_id: str):
        """Return a previously validated Arabic translation, if one exists."""
        conn = self.connect()
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("""
                SELECT translated_title, translated_summary, translation_metadata_json
                FROM news_journal WHERE news_id = ?
            """, (news_id,)).fetchone()
            if not row or not row["translated_title"] or not row["translated_summary"]:
                return None
            metadata = json.loads(row["translation_metadata_json"] or "{}")
            return {
                "title": row["translated_title"],
                "summary": row["translated_summary"],
                "metadata": metadata if isinstance(metadata, dict) else {},
            }
        finally:
            conn.close()

    def record_news_translation(self, news_id: str, translated_title: str, translated_summary: str, *, metadata=None) -> None:
        """Persist only a validated translation; never derive or alter it here."""
        conn = self.connect()
        try:
            cur = conn.execute("""
                UPDATE news_journal
                SET translated_title = ?, translated_summary = ?,
                    translation_metadata_json = ?, updated_at = ?
                WHERE news_id = ?
            """, (
                str(translated_title), str(translated_summary),
                self._json(metadata or {}), self.now().isoformat(), news_id,
            ))
            if cur.rowcount != 1:
                raise ValueError("news_journal_not_found")
            conn.commit()
        finally:
            conn.close()

    def record_news_delivery(self, news_id: str, destination, *, success=False, failure_reason=None, metadata=None) -> int:
        conn = self.connect()
        try:
            if conn.execute("SELECT 1 FROM news_journal WHERE news_id = ?", (news_id,)).fetchone() is None:
                raise ValueError("news_journal_not_found")
            cur = conn.execute("""
                INSERT INTO news_deliveries (news_id, destination, attempted_at, success, failure_reason, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (news_id, str(destination), self.now().isoformat(), int(bool(success)), failure_reason, self._json(metadata or {})))
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()

    def report_was_sent(self, report_key: str) -> bool:
        conn = self.connect()
        try:
            row = conn.execute("SELECT status FROM report_journal WHERE report_key = ?", (report_key,)).fetchone()
            return bool(row and row[0] == "SENT")
        finally:
            conn.close()

    def record_report(self, report_key, report_type, period_start, period_end, *, status="READY", metadata=None):
        conn = self.connect()
        try:
            conn.execute("""INSERT INTO report_journal (report_key, report_type, period_start, period_end, status, created_at, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(report_key) DO UPDATE SET status=excluded.status, metadata_json=excluded.metadata_json""",
                (report_key, report_type, str(period_start), str(period_end), status, self.now().isoformat(), self._json(metadata or {})))
            conn.commit()
        finally:
            conn.close()

    def get_signal_journal(self, signal_id: str):
        conn = self.connect()
        try:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM signal_journal WHERE signal_id = ?", (signal_id,)).fetchone()
            return dict(row) if row else None
        finally:
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

        # Read plan data through the same transaction.  Calling the older
        # helper here opens a second SQLite writer connection and can leave a
        # valid approval pending under concurrent/admin use.
        cur.execute("SELECT duration_days FROM plans WHERE id = ?", (plan_id,))
        plan_row = cur.fetchone()
        duration = plan_row[0] if plan_row else None
        if duration is None:
            conn.close()
            return False

        from datetime import timedelta
        start_date = self.now().strftime("%Y-%m-%d")
        end_date = (self.now() + timedelta(days=duration)).strftime("%Y-%m-%d")

        try:
            # Conditional update prevents double approval from stale buttons.
            cur.execute("""
                UPDATE subscription_requests SET status = 'approved'
                WHERE id = ? AND status = 'pending'
            """, (request_id,))
            if cur.rowcount != 1:
                conn.rollback()
                conn.close()
                return False

            # Same subscription semantics as create_subscription(), kept in
            # this transaction so request status and access cannot diverge.
            cur.execute("""
                UPDATE subscriptions SET status = 'expired'
                WHERE user_id = ? AND status = 'active'
            """, (user_id,))
            cur.execute("""
                INSERT INTO subscriptions (user_id, plan_id, start_date, end_date, status)
                VALUES (?, ?, ?, ?, 'active')
            """, (user_id, plan_id, start_date, end_date))
            cur.execute("""
                UPDATE users SET subscription_status = 'active' WHERE id = ?
            """, (user_id,))

            log_date = self.now().strftime("%Y-%m-%d %H:%M")
            cur.execute("""
                INSERT INTO subscription_logs (user_id, action, date, details)
                VALUES (?, 'approve_request', ?, ?)
            """, (user_id, log_date, f"تم قبول طلب الاشتراك رقم {request_id}"))
            conn.commit()
            conn.close()
            return True
        except Exception:
            conn.rollback()
            conn.close()
            return False

    def reject_request(self, request_id):
        """Reject one pending manual request without changing subscriptions.

        The conditional update is deliberate: a stale admin button cannot reject
        a request that another administrator has already decided.
        """
        conn = self.connect()
        try:
            row = conn.execute(
                "SELECT user_id, status FROM subscription_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
            if not row or row[1] != "pending":
                return False

            updated = conn.execute(
                "UPDATE subscription_requests SET status = 'rejected' "
                "WHERE id = ? AND status = 'pending'",
                (request_id,),
            )
            if updated.rowcount != 1:
                return False

            log_date = self.now().strftime("%Y-%m-%d %H:%M")
            conn.execute(
                "INSERT INTO subscription_logs (user_id, action, date, details) "
                "VALUES (?, 'reject_request', ?, ?)",
                (row[0], log_date, f"تم رفض طلب الاشتراك رقم {request_id}"),
            )
            conn.commit()
            return True
        finally:
            conn.close()

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

    def get_user_role(self, tg_id, *, owner_tg_id=None):
        """
        جلب دور المستخدم الحقيقي بناءً على Telegram ID.
        لأن TelegramApp يمرّر user.id وهو tg_id وليس user_id داخل قاعدة البيانات.
        """
        if owner_tg_id is not None and int(tg_id) == int(owner_tg_id):
            return "owner"
        role = self.get_setting(f"user_role_{tg_id}", "user")
        return role if role in ("admin", "user") else "user"

    def get_internal_user_id(self, tg_id):
        """Resolve the Telegram identity used by the interface to users.id."""
        conn = self.connect()
        try:
            row = conn.execute("SELECT id FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def get_user_subscription_by_tg_id(self, tg_id):
        """Return subscription state for a Telegram user without mixing ID domains."""
        user_id = self.get_internal_user_id(tg_id)
        if user_id is None:
            return {"status": "none"}
        # This performs the existing expiry transition when it is due before
        # returning the user-facing state.
        self.is_subscription_active(user_id)
        return self.get_user_subscription(user_id)

    def is_subscription_active_by_tg_id(self, tg_id):
        user_id = self.get_internal_user_id(tg_id)
        return bool(user_id is not None and self.is_subscription_active(user_id))

    def create_subscription_request_by_tg_id(self, tg_id, plan_id):
        """Create one pending manual request using existing subscription tables.

        This intentionally does not initiate a payment or grant access.
        """
        user_id = self.get_internal_user_id(tg_id)
        if user_id is None:
            return {"created": False, "reason": "user_not_registered"}
        if self.get_plan(plan_id) is None:
            return {"created": False, "reason": "plan_not_found"}

        conn = self.connect()
        try:
            pending = conn.execute(
                "SELECT id FROM subscription_requests WHERE user_id = ? AND status = 'pending' ORDER BY id DESC LIMIT 1",
                (user_id,),
            ).fetchone()
            if pending:
                return {"created": False, "reason": "pending_exists", "request_id": pending[0]}

            now = self.now().isoformat()
            cur = conn.execute(
                "INSERT INTO subscription_requests (user_id, plan_id, request_date, status) VALUES (?, ?, ?, 'pending')",
                (user_id, plan_id, now),
            )
            conn.execute(
                "INSERT INTO subscription_logs (user_id, action, date, details) VALUES (?, ?, ?, ?)",
                (user_id, "subscription_request", now, f"طلب اشتراك رقم {cur.lastrowid}"),
            )
            conn.commit()
            return {"created": True, "request_id": cur.lastrowid}
        finally:
            conn.close()

    def get_subscription_request(self, request_id):
        """Return request state for UI/tests without exposing payment data."""
        conn = self.connect()
        try:
            row = conn.execute(
                "SELECT id, user_id, plan_id, request_date, status "
                "FROM subscription_requests WHERE id = ?",
                (request_id,),
            ).fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "user_id": row[1],
                "plan_id": row[2],
                "request_date": row[3],
                "status": row[4],
            }
        finally:
            conn.close()

    def get_completed_trade_summaries(self, limit=10):
        """Read closed lifecycle records only; never infer a trade result."""
        conn = self.connect()
        try:
            rows = conn.execute(
                """
                SELECT s.symbol, s.asset_class, s.direction, t.closed_at
                FROM trade_journal t
                JOIN signal_journal s ON s.signal_id = t.signal_id
                WHERE t.status = 'CLOSED'
                ORDER BY t.closed_at DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
            return [
                {"symbol": row[0], "asset_class": row[1], "direction": row[2], "closed_at": row[3]}
                for row in rows
            ]
        finally:
            conn.close()


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

