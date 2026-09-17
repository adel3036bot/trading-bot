# ============================================================
# ADEL SMART BOT ELITE — CORE FILE
# النسخة النهائية — ImageEngine + ChartEngine + AnalysisEngine
# ============================================================
# فلسفة هذا الملف:
# - ImageEngine و ChartEngine هما طبقة العرض (Presentation Layer) فقط.
# - لا يحتويان على أي منطق تحليل أو اكتشاف أو حساب.
# - جميع البيانات (الأهداف، وقف الخسارة، منطقة الاهتمام، FVG، Order Block،
#   خطوط الاتجاه، الدعم والمقاومة، النماذج الفنية، الأسباب، إلخ) تصل جاهزة
#   من المحركات الأخرى مثل:
#   AnalysisEngine / SignalEngine / ScoringEngine / DataEngine
# - دور هذا الملف يقتصر على رسم هذه البيانات وإخراجها بصريًا بشكل احترافي.
# - إذا وصلت البيانات، يرسمها. وإذا لم تصل، لا يخمنها ولا يحسبها ولا ينشئها.

from PIL import Image, ImageDraw, ImageFont, ImageColor
import textwrap
import pandas as pd
import datetime
import os
import random
from pathlib import Path

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:  # Rendering still degrades safely when optional deps are absent.
    arabic_reshaper = None
    get_display = None

from core.events import EventType
from images.image_contract import coerce_event_type, normalize_trade_payload, validate_event_payload

# ============================================================
# 1) IMAGE ENGINE — CORE RENDERER
# ============================================================

class ImageEngine:
    def __init__(self):
        self.project_root = Path(__file__).resolve().parents[1]
        # إعدادات عامة
        self.config = {
            "canvas_width": 1400,
            "canvas_height": 1600,
            "max_width": 1100,
            "line_height": 55,
            "font_large": 38,
            "font_medium": 34,
            "font_small": 30,
            "watermark_alpha": 60,
        }

        # إعدادات الخطوط
        regular_font = self.project_root / "fonts" / "regular.ttf"
        bold_font = self.project_root / "fonts" / "bold.ttf"
        self.font_large = ImageFont.truetype(str(regular_font), self.config["font_large"])
        self.font_medium = ImageFont.truetype(str(regular_font), self.config["font_medium"])
        self.font_small = ImageFont.truetype(str(regular_font), self.config["font_small"])
        self.font_bold = ImageFont.truetype(str(bold_font), self.config["font_large"])

        # الشعار العام (إن وجد)
        logo_path = self.project_root / "templates" / "logo.png"
        self.logo = Image.open(logo_path).convert("RGBA") if logo_path.exists() else None

        # العلامة المائية (إن وجدت)
        watermark_path = self.project_root / "templates" / "watermark.png"
        if watermark_path.exists():
            self.watermark = Image.open(watermark_path).convert("RGBA")
            self.watermark.putalpha(self.config["watermark_alpha"])
        else:
            self.watermark = None

        # مصحح الإملاء
        self.spell_map = {
            "هاذا": "هذا",
            "إستاذ": "أستاذ",
            "مسؤل": "مسؤول",
            "إستثمار": "استثمار",
            "إقتصاد": "اقتصاد",
            "إستراتيجية": "استراتيجية",
            "إدارة": "إدارة",
        }

        # خريطة الأيقونات الديناميكية
        self.icon_map = {
            "CALL": str(self.project_root / "icons" / "call.png"),
            "PUT": str(self.project_root / "icons" / "put.png"),
            "NEWS": str(self.project_root / "icons" / "news.png"),
            "WARNING": str(self.project_root / "icons" / "warning.png"),
            "SUCCESS": str(self.project_root / "icons" / "success.png"),
            "FAILURE": str(self.project_root / "icons" / "failure.png"),
            "EARNINGS": str(self.project_root / "icons" / "earnings.png"),
            "HIGH_RISK": str(self.project_root / "icons" / "high_risk.png"),
            "HIGH_CONFIDENCE": str(self.project_root / "icons" / "high_confidence.png"),
        }

        # إحداثيات الحقول لكل قالب
        self.prepare_positions()

    # --------------------------------------------------------
    # إحداثيات الحقول لكل قالب
    # --------------------------------------------------------
    def prepare_positions(self):
        self.positions = {
            "contract": {
                "company_name": (80, 120),
                "symbol": (80, 180),
                "contract_type": (80, 240),
                "strike": (80, 300),
                "contract_style": (80, 360),
                "entry_price": (80, 420),
                "current_price": (80, 480),
                "expiry_date": (80, 540),
                "signal_time": (80, 600),
                "rating": (1100, 120),
                "tp1": (80, 660),
                "tp2": (80, 720),
                "tp3": (80, 780),
                "stop_loss": (80, 840),
                "profit_percent": (1100, 180),
                "market_index": (1100, 240),
                "disclaimer": (80, 900),
                "qr_code": (1100, 300),
                "company_logo": (1100, 360),
            },

            "signal": {
                "company_name": (80, 120),
                "symbol": (80, 180),
                "contract_type": (80, 240),
                "strike": (80, 300),
                "entry_price": (80, 360),
                "expiry_date": (80, 420),
                "signal_time": (80, 480),
                "rating": (1100, 120),
                "tp1": (80, 540),
                "tp2": (80, 600),
                "tp3": (80, 660),
                "stop_loss": (80, 720),
                "market_index": (1100, 180),
                "disclaimer": (80, 780),
                "qr_code": (1100, 240),
            },

            "tp_update": {
                "company_name": (80, 120),
                "symbol": (80, 180),
                "tp_level": (80, 240),
                "entry_price": (80, 300),
                "current_price": (80, 360),
                "profit_percent": (80, 420),
                "signal_time": (80, 480),
                "market_index": (80, 540),
                "status": (80, 600),
                "disclaimer": (80, 660),
            },

            "stoploss_update": {
                "company_name": (80, 120),
                "symbol": (80, 180),
                "entry_price": (80, 240),
                "stop_loss": (80, 300),
                "current_price": (80, 360),
                "loss_percent": (80, 420),
                "signal_time": (80, 480),
                "market_index": (80, 540),
                "status": (80, 600),
                "disclaimer": (80, 660),
            },

            "news": {
                "headline": (80, 120),
                "body": (80, 200),
                "category": (80, 520),
                "session": (80, 580),
                "timestamp": (80, 640),
                "source": (80, 700),
            },

            "breaking": {
                "headline": (80, 120),
                "body": (80, 220),
                "timestamp": (80, 620),
                "source": (80, 680),
            },

            "analysis": {
                "title": (80, 120),
                "summary": (80, 200),
                "trend": (80, 320),
                "supports": (80, 380),
                "resistances": (80, 460),
                "liquidity": (80, 540),
                "pattern_name": (80, 620),
                "pattern_description": (80, 680),
            },

            "daily_report": {
                "title": (80, 120),
                "date": (80, 180),
                "total_trades": (80, 240),
                "win_rate": (80, 300),
                "best_trade": (80, 360),
                "worst_trade": (80, 420),
                "total_profit": (80, 480),
                "total_loss": (80, 540),
                "summary": (80, 600),
            },

            "weekly_report": {
                "title": (80, 120),
                "week_range": (80, 180),
                "total_trades": (80, 240),
                "win_rate": (80, 300),
                "best_trade": (80, 360),
                "worst_trade": (80, 420),
                "total_profit": (80, 480),
                "total_loss": (80, 540),
                "summary": (80, 600),
            },

            "monthly_report": {
                "title": (80, 120),
                "month": (80, 180),
                "total_trades": (80, 240),
                "win_rate": (80, 300),
                "best_trade": (80, 360),
                "worst_trade": (80, 420),
                "total_profit": (80, 480),
                "total_loss": (80, 540),
                "summary": (80, 600),
            },

            # متوافق مع PerformanceEngine.build_evening_structured
            "performance": {
                "title": (80, 120),
                "date": (80, 180),
                "total_trades": (80, 240),
                "winning_trades": (80, 300),
                "losing_trades": (80, 360),
                "win_rate": (80, 420),
                "average_profit": (80, 480),
                "total_profit": (80, 540),
                "moon_shots": (80, 600),
                "legendary_trades": (80, 660),
                "best_symbol": (80, 720),
                "summary": (80, 780),
            },

            "chart": {
                "title": (80, 80),
                "symbol": (80, 140),
                "timeframe": (80, 200),
                "trend": (80, 260),
                "pattern_name": (80, 320),
                "pattern_description": (80, 380),
                "comment": (80, 440),
            },

            "moonshot": {
                "title": (80, 120),
                "symbol": (80, 180),
                "reason": (80, 240),
                "entry_price": (80, 300),
                "targets": (80, 360),
                "risk": (80, 420),
                "summary": (80, 480),
            },

            "legendary": {
                "title": (80, 120),
                "symbol": (80, 180),
                "entry_price": (80, 240),
                "exit_price": (80, 300),
                "profit_percent": (80, 360),
                "summary": (80, 420),
            },

            "god_mode": {
                "title": (80, 120),
                "symbol": (80, 180),
                "entry_price": (80, 240),
                "current_price": (80, 300),
                "profit_percent": (80, 360),
                "summary": (80, 420),
            },

            "open_profit": {
                "title": (80, 120),
                "symbol": (80, 180),
                "current_price": (80, 240),
                "profit_percent": (80, 300),
                "summary": (80, 360),
            },
        }

    # --------------------------------------------------------
    # تنظيف النص واختيار الخط المناسب
    # --------------------------------------------------------
    def clean_text(self, text: str) -> str:
        if not isinstance(text, str):
            text = str(text)
        for wrong, correct in self.spell_map.items():
            text = text.replace(wrong, correct)
        return text

    def responsive_font(self, text: str):
        length = len(text)
        if length > 600:
            return self.font_small
        elif length > 300:
            return self.font_medium
        else:
            return self.font_large

    # --------------------------------------------------------
    # رسم بلوك نصي (RTL / LTR)
    # --------------------------------------------------------
    def prepare_rtl_text(self, text: str) -> str:
        """Prepare logical Arabic/Latin text for Pillow's non-RAQM renderer.

        Payload values remain logical Unicode everywhere outside this
        presentation boundary. Cairo provides the Arabic glyphs; reshaping
        and BiDi ordering are required here because this Pillow build has no
        native RAQM/FriBidi text-layout support.
        """
        text = self.clean_text(text)
        if arabic_reshaper and get_display:
            return get_display(arabic_reshaper.reshape(text))
        return text

    def draw_text_block(self, img, text, x, y, max_width=None, rtl=True):
        text = self.clean_text(text)
        font = self.responsive_font(text)
        draw = ImageDraw.Draw(img)

        if max_width is None:
            max_width = self.config["max_width"]

        wrapped = textwrap.wrap(text, width=40)

        for line in wrapped:
            if rtl:
                # PIL does not shape Arabic glyphs by itself.  Shape only at
                # presentation time; the News/Signal payload remains logical
                # Unicode and keeps symbols/numbers intact for Telegram.
                display_line = self.prepare_rtl_text(line)
                draw.text((x, y), display_line, font=font, fill="white", anchor="ra")
            else:
                draw.text((x, y), line, font=font, fill="white")
            y += self.config["line_height"]

        return img

    # --------------------------------------------------------
    # رسم حقل واحد حسب القالب
    # --------------------------------------------------------
    def draw_field(self, img, field_name, value, template_type):
        if template_type not in self.positions:
            return img

        if field_name not in self.positions[template_type]:
            return img

        x, y = self.positions[template_type][field_name]
        return self.draw_text_block(img, str(value), x, y, rtl=True)

    # --------------------------------------------------------
    # العناصر المشتركة (شعار، QR، أيقونات، علامة مائية)
    # --------------------------------------------------------
    def merge_common_elements(self, img, data):
        # العلامة المائية في المنتصف بنفس الدرجة في جميع الصور
        if self.watermark is not None:
            wm = self.watermark.copy()
            target_w = int(self.config["canvas_width"] * 0.55)
            target_h = int(self.config["canvas_height"] * 0.55)
            wm = wm.resize((target_w, target_h))
            wm.putalpha(self.config["watermark_alpha"])
            x = (img.width - target_w) // 2
            y = (img.height - target_h) // 2
            img.paste(wm, (x, y), wm)

        # الشعار العام
        if self.logo is not None:
            logo_resized = self.logo.resize((140, 140))
            img.paste(logo_resized, (img.width - 180, img.height - 180), logo_resized)

        # شعار الشركة
        if "company_logo_path" in data and os.path.exists(data["company_logo_path"]):
            company_logo = Image.open(data["company_logo_path"]).convert("RGBA")
            company_logo = company_logo.resize((120, 120))
            img.paste(company_logo, (img.width - 180, 40), company_logo)

        # QR Code
        if "qr_code_path" in data and os.path.exists(data["qr_code_path"]):
            qr = Image.open(data["qr_code_path"]).convert("RGBA")
            qr = qr.resize((140, 140))
            img.paste(qr, (img.width - 180, img.height - 340), qr)

        # أيقونة ديناميكية (CALL / PUT / Earnings / Warning ...)
        if "icon" in data:
            icon_key = data["icon"]
            icon_path = self.icon_map.get(icon_key)
            if icon_path and os.path.exists(icon_path):
                icon_img = Image.open(icon_path).convert("RGBA")
                icon_img = icon_img.resize((80, 80))
                img.paste(icon_img, (40, img.height - 140), icon_img)

        return img

    # --------------------------------------------------------
    # رسم الخلفية الديناميكية بالكامل
    # --------------------------------------------------------
    def _draw_background(self, template_type: str):
        w = self.config["canvas_width"]
        h = self.config["canvas_height"]

        # خلفية أساسية داكنة
        img = Image.new("RGBA", (w, h), "#050509")
        draw = ImageDraw.Draw(img)

        # اختيار ألوان التدرج حسب نوع القالب
        if template_type in ("news", "breaking", "economic", "market", "premarket", "aftermarket", "critical"):
            top_color = "#0b1f3f"
            bottom_color = "#123c7a"

        elif template_type in ("contract", "signal"):
            top_color = "#050509"
            bottom_color = "#202020"

        elif template_type in ("tp_update", "stoploss_update", "moonshot", "legendary", "god_mode", "open_profit"):
            top_color = "#1b1030"
            bottom_color = "#3b1f70"

        elif template_type in ("daily_report", "weekly_report", "monthly_report", "performance"):
            top_color = "#0b1f3f"
            bottom_color = "#1b4f7a"

        elif template_type in ("analysis", "chart"):
            top_color = "#050509"
            bottom_color = "#182033"

        else:
            top_color = "#050509"
            bottom_color = "#202020"

        # تدرج لوني ناعم (Gradient Mesh)
        r1, g1, b1 = ImageColor.getrgb(top_color)
        r2, g2, b2 = ImageColor.getrgb(bottom_color)

        for i in range(h):
            ratio = i / h
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            draw.line([(0, i), (w, i)], fill=(r, g, b, 255))

        # طبقة إضاءة خفيفة من الأعلى
        light_top = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        lt_draw = ImageDraw.Draw(light_top)
        lt_draw.rectangle([0, 0, w, int(h * 0.25)], fill=(255, 255, 255, 25))
        img = Image.alpha_composite(img, light_top)

        # طبقة إضاءة خفيفة من الأسفل
        light_bottom = Image.new("RGBA", (w, h), (255, 255, 255, 0))
        lb_draw = ImageDraw.Draw(light_bottom)
        lb_draw.rectangle([0, int(h * 0.75), w, h], fill=(255, 255, 255, 20))
        img = Image.alpha_composite(img, light_bottom)

        # طبقة Noise خفيفة جدًا (راحة للعين)
        noise = Image.new("RGBA", (w, h))
        noise_pixels = noise.load()

        for y in range(h):
            for x in range(w):
                val = random.randint(0, 12)
                noise_pixels[x, y] = (val, val, val, 18)

        img = Image.alpha_composite(img, noise)

        # طبقة Soft Light (نعومة الخلفية)
        soft = Image.new("RGBA", (w, h), (255, 255, 255, 30))
        img = Image.alpha_composite(img, soft)

        # إطار خارجي مع Glow بسيط
        frame = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        f_draw = ImageDraw.Draw(frame)
        f_draw.rectangle([20, 20, w - 20, h - 20], outline="#3fa9f5", width=3)
        img = Image.alpha_composite(img, frame)

        glow = Image.new("RGBA", (w, h), (63, 169, 245, 18))
        img = Image.alpha_composite(img, glow)

        # بانر علوي
        banner_top = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        bt_draw = ImageDraw.Draw(banner_top)
        bt_draw.rectangle([40, 40, w - 40, 160], fill="#0b1220")
        bt_draw.rectangle([40, 40, w - 40, 160], outline="#3fa9f5", width=2)
        img = Image.alpha_composite(img, banner_top)

        # بانر سفلي
        banner_bottom = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        bb_draw = ImageDraw.Draw(banner_bottom)
        bb_draw.rectangle([40, h - 140, w - 40, h - 60], fill="#101520")
        bb_draw.rectangle([40, h - 140, w - 40, h - 60], outline="#3fa9f5", width=2)
        img = Image.alpha_composite(img, banner_bottom)

        # نص التحذير
        warning_text = (
            "⚠️ هذه إشارة وقراءة فنية لأغراض تعليمية فقط، "
            "وليست توصية مباشرة للشراء أو البيع."
        )

        font_warn = ImageFont.truetype(str(self.project_root / "fonts" / "regular.ttf"), 26)
        draw = ImageDraw.Draw(img)
        draw.text((w // 2, h - 110), warning_text, font=font_warn, fill="#ffcc00", anchor="mm")

        return img

    # --------------------------------------------------------
    # بناء صورة القالب حسب النوع والبيانات
    # --------------------------------------------------------
    def build_template_image(self, template_type, data):
        if template_type == "contract":
            return self._build_contract_signal(data)
        base = self._draw_background(template_type)
        img = self.merge_common_elements(base, data)

        if template_type in self.positions:
            for field_name in self.positions[template_type].keys():
                if field_name in data and data[field_name] not in (None, ""):
                    img = self.draw_field(img, field_name, data[field_name], template_type)

        return img

    def _build_contract_signal(self, data):
        """Options card renderer. Values are ready payload values only."""
        w, h = 1400, 1600
        img = Image.new("RGBA", (w, h), "#05070d")
        draw = ImageDraw.Draw(img)
        blue, green, red, gold, purple = "#158cff", "#16c784", "#dc3545", "#d9a928", "#8e44ff"
        draw.rounded_rectangle((28, 28, w - 28, h - 28), 28, outline=blue, width=4)
        draw.line((60, 180, w - 60, 180), fill=blue, width=2)
        draw.text((w // 2, 72), "ADEL SMART BOT ELITE", font=self.font_bold, fill="white", anchor="ma")
        draw.text((w // 2, 128), "عقد مقترح للمراقبة", font=self.font_medium, fill=gold, anchor="ma")
        name = data.get("company_name") or data.get("symbol") or "—"
        symbol = data.get("symbol", "—")
        draw.text((80, 235), str(name), font=self.font_bold, fill="white")
        draw.text((80, 295), str(symbol), font=self.font_medium, fill=blue)
        rating = str(data.get("rating") or "—")
        draw.rounded_rectangle((1060, 220, 1300, 350), 20, outline=purple, width=3)
        draw.text((1180, 245), "التقييم", font=self.font_small, fill="white", anchor="ma")
        draw.text((1180, 290), rating, font=self.font_bold, fill=purple, anchor="ma")
        fields = [
            ("سعر الدخول", data.get("entry_price"), blue),
            ("تاريخ الانتهاء", data.get("expiry_date"), gold),
            ("نوع العقد", data.get("contract_type"), green if str(data.get("contract_type", "")).upper() == "CALL" else red),
            ("العقد / Strike", f"{data.get('contract_style', '')} {data.get('strike', '')}", "white"),
        ]
        y = 390
        for label, value, color in fields:
            draw.rounded_rectangle((70, y, 1330, y + 105), 16, outline="#34445f", width=2)
            draw.text((1280, y + 18), label, font=self.font_small, fill="#a9c7ef", anchor="ra")
            draw.text((1280, y + 55), str(value or "—"), font=self.font_medium, fill=color, anchor="ra")
            y += 125
        draw.text((1280, 900), "الأهداف", font=self.font_medium, fill=green, anchor="ra")
        for i, key in enumerate(("tp1", "tp2", "tp3")):
            yy = 950 + i * 80
            draw.rounded_rectangle((70, yy, 860, yy + 58), 12, outline=green, width=2)
            draw.text((810, yy + 10), f"TP{i + 1}: {data.get(key) or '—'}", font=self.font_small, fill=green, anchor="ra")
        draw.rounded_rectangle((890, 950, 1330, 1168), 16, outline=red, width=3)
        draw.text((1280, 980), "وقف الخسارة", font=self.font_small, fill=red, anchor="ra")
        draw.text((1280, 1040), str(data.get("stop_loss") or "—"), font=self.font_bold, fill=red, anchor="ra")
        draw.text((1280, 1220), "حالة السوق", font=self.font_small, fill="#a9c7ef", anchor="ra")
        draw.text((1280, 1265), str(data.get("market_index") or "SPX | QQQ | SPY | NASDAQ: غير متاح"), font=self.font_small, fill="white", anchor="ra")
        draw.text((1280, 1325), f"وقت الإشارة: {data.get('signal_time') or '—'}", font=self.font_small, fill="#a9c7ef", anchor="ra")
        note = data.get("important_notes") or data.get("disclaimer")
        if note:
            draw.text((1280, 1430), str(note), font=self.font_small, fill="#d5dce8", anchor="ra")
        return img

    # --------------------------------------------------------
    # التصدير إلى ملف
    # --------------------------------------------------------
    def export(self, img, filename=None):
        if filename is None:
            filename = self.project_root / "output" / f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path)
        return str(output_path)

    # --------------------------------------------------------
    # بناء صورة كاملة مباشرة
    # --------------------------------------------------------
    def build_image(self, template_type, data, filename=None):
        img = self.build_template_image(template_type, data)
        return self.export(img, filename)

    # ============================================================
    # TRADE EVENT → IMAGE GENERATOR (TP / SL / MOONSHOT / LEGENDARY / GOD MODE / OPEN PROFIT)
    # ============================================================
    def generate(self, event_type, trade, filename=None):
        event_type = coerce_event_type(event_type)
        trade = normalize_trade_payload(trade)
        validate_event_payload(event_type, trade)

        template_type = "contract"
        data = {}

        base_name = trade.get("company_name") or trade.get("symbol") or ""
        symbol = trade.get("symbol", "")
        entry_price = trade.get("entry_price")
        current_price = trade.get("current_price")
        profit = trade.get("profit")
        market_index = trade.get("market_index", "")
        signal_time = trade.get("signal_time", "")
        expiry_date = trade.get("expiry_date", "")

        # TP EVENTS
        if event_type in (EventType.TP1, EventType.TP2, EventType.TP3):
            template_type = "tp_update"
            tp_label = event_type.value
            data = {
                "company_name": base_name,
                "symbol": symbol,
                "tp_level": tp_label,
                "entry_price": entry_price,
                "current_price": current_price,
                "profit_percent": f"{profit:.2f}%" if isinstance(profit, (int, float)) else "",
                "signal_time": signal_time,
                "market_index": market_index,
                "status": "Hit",
                "disclaimer": "هذه قراءة فنية تعليمية وليست توصية مباشرة.",
            }

        # STOP LOSS
        elif event_type == EventType.STOP_LOSS:
            template_type = "stoploss_update"
            data = {
                "company_name": base_name,
                "symbol": symbol,
                "entry_price": entry_price,
                "stop_loss": trade.get("stop_loss"),
                "current_price": current_price,
                "loss_percent": f"{profit:.2f}%" if isinstance(profit, (int, float)) else "",
                "signal_time": signal_time,
                "market_index": market_index,
                "status": "Stopped",
                "disclaimer": "هذه قراءة فنية تعليمية وليست توصية مباشرة.",
            }

        # MOONSHOT
        elif event_type == EventType.MOONSHOT:
            template_type = "moonshot"
            data = {
                "title": "MOONSHOT ALERT 🚀",
                "symbol": symbol,
                "reason": trade.get("reason", ""),
                "entry_price": entry_price,
                "targets": trade.get("targets", ""),
                "risk": trade.get("risk", ""),
                "summary": f"الربح الحالي: {profit:.2f}%" if isinstance(profit, (int, float)) else "",
            }

        # LEGENDARY
        elif event_type == EventType.LEGENDARY:
            template_type = "legendary"
            data = {
                "title": "LEGENDARY TRADE 🏆",
                "symbol": symbol,
                "entry_price": entry_price,
                "exit_price": current_price,
                "profit_percent": f"{profit:.2f}%" if isinstance(profit, (int, float)) else "",
                "summary": trade.get("summary", ""),
            }

        # GOD MODE
        elif event_type == EventType.GOD_MODE:
            template_type = "god_mode"
            data = {
                "title": "⚡ GOD MODE",
                "symbol": symbol,
                "entry_price": entry_price,
                "current_price": current_price,
                "profit_percent": f"{profit:.2f}%" if isinstance(profit, (int, float)) else "",
                "summary": trade.get("summary", ""),
            }

        # OPEN PROFIT
        elif event_type == EventType.OPEN_PROFIT:
            template_type = "open_profit"
            data = {
                "title": "📈 OPEN PROFIT",
                "symbol": symbol,
                "current_price": current_price,
                "profit_percent": f"{profit:.2f}%" if isinstance(profit, (int, float)) else "",
                "summary": trade.get("summary", ""),
            }

        # PROGRESS UPDATE
        elif event_type == EventType.PROGRESS_UPDATE:
            template_type = "performance"
            data = {
                "title": "تقدم الصفقة",
                "date": trade.get("date") or signal_time,
                "total_trades": trade.get("total_trades"),
                "winning_trades": trade.get("winning_trades"),
                "losing_trades": trade.get("losing_trades"),
                "win_rate": trade.get("win_rate"),
                "average_profit": trade.get("average_profit"),
                "total_profit": trade.get("total_profit"),
                "moon_shots": trade.get("moon_shots"),
                "legendary_trades": trade.get("legendary_trades"),
                "best_symbol": trade.get("best_symbol"),
                "summary": trade.get("progress_text", ""),
            }

        # DEFAULT CONTRACT
        else:
            template_type = "contract"
            data = {
                "company_name": base_name,
                "symbol": symbol,
                "contract_type": trade.get("contract_type", ""),
                "strike": trade.get("strike", ""),
                "contract_style": trade.get("contract_style", ""),
                "entry_price": entry_price,
                "current_price": current_price,
                "expiry_date": expiry_date,
                "signal_time": signal_time,
                "rating": trade.get("rating", ""),
                "tp1": trade.get("tp1", ""),
                "tp2": trade.get("tp2", ""),
                "tp3": trade.get("tp3", ""),
                "stop_loss": trade.get("stop_loss", ""),
                "profit_percent": f"{profit:.2f}%" if isinstance(profit, (int, float)) else "",
                "market_index": market_index,
                "disclaimer": "هذه قراءة فنية تعليمية وليست توصية مباشرة.",
            }

        img = self.build_template_image(template_type, data)
        return self.export(img, filename)

# ============================================================
# 2) CHART ENGINE — MARKET VISUALIZATION
# ============================================================

class ChartEngine:
    def __init__(self):
        self.config = {
            "width": 1400,
            "height": 900,
            "candle_width": 12,
            "candle_gap": 4,
            "bull_color": "#00ff88",
            "bear_color": "#ff4d4d",
            "wick_color": "#ffffff",
            "background_color": "#0f0f0f",
            "indicator_color": "#00aaff",
            "support_color": "#00ff00",
            "resistance_color": "#ff0000",
            "liquidity_color": "#8844ff",
            "interest_zone_color": "#0088ff",
            "fvg_color": "#ffaa00",
            "order_block_color": "#ff00aa",
            "pattern_color": "#ffffff",
            "reason_box_bg": "#111111",
            "reason_box_border": "#ffaa00",
            "warning_bar_bg": "#222222",
            "warning_bar_text": "#ffcc00",
            "timeframe_text_color": "#ffffff",
        }

        self.df = None

    # --------------------------------------------------------
    # تحميل بيانات السوق
    # --------------------------------------------------------
    def load_market_data(self, df):
        self.df = df.copy()

    # --------------------------------------------------------
    # تحويل السعر إلى إحداثي Y
    # --------------------------------------------------------
    def price_to_y(self, price, max_price, min_price):
        if max_price == min_price:
            return self.config["height"] // 2

        return self.config["height"] - int(
            (price - min_price) / (max_price - min_price) * self.config["height"]
        )

    # --------------------------------------------------------
    # رسم شمعة واحدة
    # --------------------------------------------------------
    def draw_candle(self, draw, index, o, h, l, c, max_price, min_price):
        x = index * (self.config["candle_width"] + self.config["candle_gap"]) + 80

        color = self.config["bull_color"] if c >= o else self.config["bear_color"]

        y_open = self.price_to_y(o, max_price, min_price)
        y_close = self.price_to_y(c, max_price, min_price)
        y_high = self.price_to_y(h, max_price, min_price)
        y_low = self.price_to_y(l, max_price, min_price)

        draw.rectangle(
            [x, min(y_open, y_close), x + self.config["candle_width"], max(y_open, y_close)],
            fill=color,
        )

        draw.line(
            [x + self.config["candle_width"] // 2, y_high,
             x + self.config["candle_width"] // 2, y_low],
            fill=self.config["wick_color"],
            width=2,
        )

    # --------------------------------------------------------
    # رسم جميع الشموع
    # --------------------------------------------------------
    def draw_candles(self, img):
        draw = ImageDraw.Draw(img)

        max_price = self.df["High"].max()
        min_price = self.df["Low"].min()

        for i, row in self.df.iterrows():
            self.draw_candle(
                draw,
                i,
                row["Open"],
                row["High"],
                row["Low"],
                row["Close"],
                max_price,
                min_price,
            )

        return img

    # --------------------------------------------------------
    # رسم المتوسط المتحرك
    # --------------------------------------------------------
    def draw_moving_average(self, img, period=20):
        draw = ImageDraw.Draw(img)

        if len(self.df) < period:
            return img

        ma = self.df["Close"].rolling(period).mean()

        max_price = self.df["High"].max()
        min_price = self.df["Low"].min()

        prev_point = None

        for i, value in enumerate(ma):
            if pd.isna(value):
                continue

            x = i * (self.config["candle_width"] + self.config["candle_gap"]) + 80
            y = self.price_to_y(value, max_price, min_price)

            if prev_point:
                draw.line([prev_point, (x, y)], fill=self.config["indicator_color"], width=3)

            prev_point = (x, y)

        return img

    # --------------------------------------------------------
    # رسم مستويات الدعم والمقاومة
    # --------------------------------------------------------
    def draw_levels(self, img, supports=None, resistances=None):
        draw = ImageDraw.Draw(img)

        supports = supports or []
        resistances = resistances or []

        max_price = self.df["High"].max()
        min_price = self.df["Low"].min()

        for s in supports:
            y = self.price_to_y(s, max_price, min_price)
            draw.line([0, y, self.config["width"], y], fill=self.config["support_color"], width=2)

        for r in resistances:
            y = self.price_to_y(r, max_price, min_price)
            draw.line([0, y, self.config["width"], y], fill=self.config["resistance_color"], width=2)

        return img

    # --------------------------------------------------------
    # رسم منطقة الاهتمام
    # --------------------------------------------------------
    def draw_interest_zone(self, img, interest_zone=None):
        if not interest_zone:
            return img

        draw = ImageDraw.Draw(img)
        max_price = self.df["High"].max()
        min_price = self.df["Low"].min()

        low = interest_zone.get("low")
        high = interest_zone.get("high")
        start_index = interest_zone.get("start_index", 0)
        end_index = interest_zone.get("end_index", len(self.df) - 1)

        y_low = self.price_to_y(low, max_price, min_price)
        y_high = self.price_to_y(high, max_price, min_price)

        x_start = start_index * (self.config["candle_width"] + self.config["candle_gap"]) + 80
        x_end = end_index * (self.config["candle_width"] + self.config["candle_gap"]) + 80 + self.config["candle_width"]

        draw.rectangle(
            [x_start, y_high, x_end, y_low],
            outline=self.config["interest_zone_color"],
            width=2,
        )

        arrow_x = x_start - 40
        arrow_y = (y_high + y_low) // 2
        draw.line([arrow_x, arrow_y, x_start, arrow_y], fill=self.config["interest_zone_color"], width=3)
        draw.polygon(
            [(x_start, arrow_y),
             (x_start - 10, arrow_y - 5),
             (x_start - 10, arrow_y + 5)],
            fill=self.config["interest_zone_color"],
        )

        return img

    # --------------------------------------------------------
    # رسم مناطق FVG
    # --------------------------------------------------------
    def draw_fvg_zones(self, img, fvg_zones=None):
        if not fvg_zones:
            return img

        draw = ImageDraw.Draw(img)
        max_price = self.df["High"].max()
        min_price = self.df["Low"].min()

        for zone in fvg_zones:
            low = zone.get("low")
            high = zone.get("high")
            start_index = zone.get("start_index", 0)
            end_index = zone.get("end_index", len(self.df) - 1)

            y_low = self.price_to_y(low, max_price, min_price)
            y_high = self.price_to_y(high, max_price, min_price)

            x_start = start_index * (self.config["candle_width"] + self.config["candle_gap"]) + 80
            x_end = end_index * (self.config["candle_width"] + self.config["candle_gap"]) + 80 + self.config["candle_width"]

            draw.rectangle(
                [x_start, y_high, x_end, y_low],
                outline=self.config["fvg_color"],
                width=2,
            )

        return img

    # --------------------------------------------------------
    # رسم مناطق Order Blocks
    # --------------------------------------------------------
    def draw_order_blocks(self, img, order_blocks=None):
        if not order_blocks:
            return img

        draw = ImageDraw.Draw(img)
        max_price = self.df["High"].max()
        min_price = self.df["Low"].min()

        for ob in order_blocks:
            low = ob.get("low")
            high = ob.get("high")
            start_index = ob.get("start_index", 0)
            end_index = ob.get("end_index", len(self.df) - 1)

            y_low = self.price_to_y(low, max_price, min_price)
            y_high = self.price_to_y(high, max_price, min_price)

            x_start = start_index * (self.config["candle_width"] + self.config["candle_gap"]) + 80
            x_end = end_index * (self.config["candle_width"] + self.config["candle_gap"]) + 80 + self.config["candle_width"]

            draw.rectangle(
                [x_start, y_high, x_end, y_low],
                outline=self.config["order_block_color"],
                width=2,
            )

        return img

    # --------------------------------------------------------
    # رسم مناطق السيولة
    # --------------------------------------------------------
    def draw_liquidity_zones(self, img, liquidity_zones=None):
        if not liquidity_zones:
            return img

        draw = ImageDraw.Draw(img)
        max_price = self.df["High"].max()
        min_price = self.df["Low"].min()

        for zone in liquidity_zones:
            price = zone.get("price")
            y = self.price_to_y(price, max_price, min_price)
            draw.line([0, y, self.config["width"], y], fill=self.config["liquidity_color"], width=1)

        return img

    # --------------------------------------------------------
    # رسم خطوط الاتجاه
    # --------------------------------------------------------
    def draw_trendlines(self, img, trendlines=None):
        if not trendlines:
            return img

        draw = ImageDraw.Draw(img)
        max_price = self.df["High"].max()
        min_price = self.df["Low"].min()

        for tl in trendlines:
            si = tl.get("start_index", 0)
            ei = tl.get("end_index", 0)
            sp = tl.get("start_price")
            ep = tl.get("end_price")

            x1 = si * (self.config["candle_width"] + self.config["candle_gap"]) + 80
            x2 = ei * (self.config["candle_width"] + self.config["candle_gap"]) + 80
            y1 = self.price_to_y(sp, max_price, min_price)
            y2 = self.price_to_y(ep, max_price, min_price)

            draw.line([x1, y1, x2, y2], fill="#ffffff", width=2)

        return img

    # --------------------------------------------------------
    # رسم النمط الفني (خطوط)
    # --------------------------------------------------------
    def draw_pattern(self, img, pattern=None):
        if not pattern:
            return img

        draw = ImageDraw.Draw(img)
        max_price = self.df["High"].max()
        min_price = self.df["Low"].min()

        lines = pattern.get("lines", [])
        for seg in lines:
            si = seg.get("start_index", 0)
            ei = seg.get("end_index", 0)
            sp = seg.get("start_price")
            ep = seg.get("end_price")

            x1 = si * (self.config["candle_width"] + self.config["candle_gap"]) + 80
            x2 = ei * (self.config["candle_width"] + self.config["candle_gap"]) + 80
            y1 = self.price_to_y(sp, max_price, min_price)
            y2 = self.price_to_y(ep, max_price, min_price)

            draw.line([x1, y1, x2, y2], fill=self.config["pattern_color"], width=2)

        return img

    # --------------------------------------------------------
    # بطاقة النمط الفني + الفريم
    # --------------------------------------------------------
    def draw_pattern_card(self, img, pattern_info=None, timeframe=None):
        if not pattern_info and not timeframe:
            return img

        draw = ImageDraw.Draw(img)
        card_x = 40
        card_y = 40
        card_w = 480
        card_h = 180

        draw.rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            fill="#111111",
            outline="#ffaa00",
            width=2,
        )

        font_title = ImageFont.truetype("fonts/bold.ttf", 32)
        font_desc = ImageFont.truetype("fonts/regular.ttf", 26)
        font_tf = ImageFont.truetype("fonts/regular.ttf", 24)

        ty = card_y + 20

        if pattern_info:
            title = pattern_info.get("name", "")
            desc = pattern_info.get("description", "")
            draw.text((card_x + 20, ty), title, font=font_title, fill="#ffffff")
            ty += 50
            wrapped = textwrap.wrap(desc, width=28)
            for line in wrapped:
                draw.text((card_x + 20, ty), line, font=font_desc, fill="#cccccc")
                ty += 32

        if timeframe:
            tf_text = f"الفريم: {timeframe}"
            draw.text((card_x + 20, card_y + card_h - 40), tf_text, font=font_tf, fill=self.config["timeframe_text_color"])

        return img

    # --------------------------------------------------------
    # صندوق الأسباب (ما الذي تحقق؟)
    # --------------------------------------------------------
    def draw_reasons_box(self, img, reasons=None):
        if not reasons:
            return img

        draw = ImageDraw.Draw(img)
        box_w = 520
        box_h = 260
        box_x = self.config["width"] - box_w - 40
        box_y = 80

        draw.rectangle(
            [box_x, box_y, box_x + box_w, box_y + box_h],
            fill=self.config["reason_box_bg"],
            outline=self.config["reason_box_border"],
            width=2,
        )

        font_title = ImageFont.truetype("fonts/bold.ttf", 30)
        font_item = ImageFont.truetype("fonts/regular.ttf", 26)

        draw.text((box_x + 20, box_y + 20), "ما الذي تحقق؟", font=font_title, fill="#ffffff")

        ty = box_y + 70
        for r in reasons:
            text = f"✅ {r}"
            draw.text((box_x + 20, ty), text, font=font_item, fill="#00ff88")
            ty += 32

        return img

    # --------------------------------------------------------
    # شريط التحذير السفلي
    # --------------------------------------------------------
    def draw_warning_bar(self, img):
        draw = ImageDraw.Draw(img)
        bar_h = 60
        bar_y = self.config["height"] - bar_h

        draw.rectangle(
            [0, bar_y, self.config["width"], self.config["height"]],
            fill=self.config["warning_bar_bg"],
        )

        font = ImageFont.truetype("fonts/regular.ttf", 26)
        text = (
            "⚠️ هذه إشارة وقراءة فنية لأغراض تعليمية فقط، "
            "وليست توصية مباشرة للشراء أو البيع. القرار الاستثماري مسؤولية المتداول."
        )
        draw.text((40, bar_y + 16), text, font=font, fill=self.config["warning_bar_text"])

        return img

    # --------------------------------------------------------
    # بناء الشارت الكامل
    # --------------------------------------------------------
    def build_chart(
        self,
        supports=None,
        resistances=None,
        interest_zone=None,
        fvg_zones=None,
        order_blocks=None,
        liquidity_zones=None,
        trendlines=None,
        pattern=None,
        pattern_info=None,
        reasons=None,
        timeframe=None,
    ):
        if self.df is None:
            raise ValueError("Market data not loaded. Call load_market_data() first.")

        img = Image.new("RGB", (self.config["width"], self.config["height"]), self.config["background_color"])

        img = self.draw_candles(img)
        img = self.draw_moving_average(img)
        img = self.draw_levels(img, supports, resistances)
        img = self.draw_interest_zone(img, interest_zone)
        img = self.draw_fvg_zones(img, fvg_zones)
        img = self.draw_order_blocks(img, order_blocks)
        img = self.draw_liquidity_zones(img, liquidity_zones)
        img = self.draw_trendlines(img, trendlines)
        img = self.draw_pattern(img, pattern)
        img = self.draw_pattern_card(img, pattern_info, timeframe)
        img = self.draw_reasons_box(img, reasons)
        img = self.draw_warning_bar(img)

        return img

# ============================================================
# 3) ANALYSIS ENGINE — MARKET STRUCTURE DETECTION
# ============================================================

class AnalysisEngine:
    def __init__(self):
        self.config = {
            "trend_period": 20,
            "support_window": 10,
            "resistance_window": 10,
        }

        self.df = None

    # --------------------------------------------------------
    # تحميل بيانات السوق
    # --------------------------------------------------------
    def load_market_data(self, df):
        self.df = df.copy()

    def ensure_data_loaded(self):
        if self.df is None:
            raise ValueError("Market data not loaded. Call load_market_data() first.")

    # --------------------------------------------------------
    # كشف الاتجاه العام
    # --------------------------------------------------------
    def detect_trend(self):
        self.ensure_data_loaded()

        close = self.df["Close"]

        if len(close) < self.config["trend_period"]:
            return "Trend: Not enough data"

        ma = close.rolling(self.config["trend_period"]).mean()

        if close.iloc[-1] > ma.iloc[-1]:
            return "Trend: Bullish"
        elif close.iloc[-1] < ma.iloc[-1]:
            return "Trend: Bearish"
        else:
            return "Trend: Sideways"

    # --------------------------------------------------------
    # كشف مستويات الدعم
    # --------------------------------------------------------
    def detect_support_levels(self):
        self.ensure_data_loaded()

        lows = self.df["Low"]
        window = self.config["support_window"]

        supports = []

        for i in range(window, len(lows) - window):
            segment = lows[i - window:i + window]
            if lows[i] == segment.min():
                supports.append(lows[i])

        return supports[-5:]

    # --------------------------------------------------------
    # كشف مستويات المقاومة
    # --------------------------------------------------------
    def detect_resistance_levels(self):
        self.ensure_data_loaded()

        highs = self.df["High"]
        window = self.config["resistance_window"]

        resistances = []

        for i in range(window, len(highs) - window):
            segment = highs[i - window:i + window]
            if highs[i] == segment.max():
                resistances.append(highs[i])

        return resistances[-5:]

    # --------------------------------------------------------
    # كشف مناطق السيولة (High / Low)
    # --------------------------------------------------------
    def detect_liquidity(self):
        self.ensure_data_loaded()

        highs = self.df["High"]
        lows = self.df["Low"]

        liquidity_zones = []

        for i in range(2, len(highs) - 2):
            if highs[i] == max(highs[i - 2:i + 3]):
                liquidity_zones.append(("Liquidity High", highs[i]))

            if lows[i] == min(lows[i - 2:i + 3]):
                liquidity_zones.append(("Liquidity Low", lows[i]))

        return liquidity_zones[-10:]

    # --------------------------------------------------------
    # توليد نص التحليل النهائي
    # --------------------------------------------------------
    def generate_analysis(self):
        self.ensure_data_loaded()

        trend = self.detect_trend()
        supports = self.detect_support_levels()
        resistances = self.detect_resistance_levels()
        liquidity = self.detect_liquidity()

        analysis_text = f"{trend}\n\n"

        analysis_text += "Support Levels:\n"
        for s in supports:
            analysis_text += f"- {s}\n"

        analysis_text += "\nResistance Levels:\n"
        for r in resistances:
            analysis_text += f"- {r}\n"

        analysis_text += "\nLiquidity Zones:\n"
        for label, price in liquidity:
            analysis_text += f"- {label}: {price}\n"

        return analysis_text
