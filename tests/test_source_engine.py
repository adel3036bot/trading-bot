import unittest
import pandas as pd
from unittest.mock import MagicMock
from engine.source_engine import SourceEngine

class TestSourceEngine(unittest.TestCase):
    
    def setUp(self):
        """إعداد بيئة الاختبار باستخدام بيانات DataFrame حقيقية الهيكل"""
        self.mock_p1 = MagicMock()
        self.mock_p2 = MagicMock()
        self.providers = {"P1": self.mock_p1, "P2": self.mock_p2}
        self.engine = SourceEngine({}, self.providers)
        
        # هيكل بيانات قياسي للنجاح
        self.valid_df = pd.DataFrame([{
            "Open": 100.0, "High": 105.0, "Low": 99.0, "Close": 102.0, "Volume": 1000
        }])

    def test_fallback_logic(self):
        """اختبار انتقال المحرك من مصدر فاشل (None) إلى مصدر ناجح (DataFrame)"""
        self.mock_p1.fetch_stock_data.return_value = None
        self.mock_p2.fetch_stock_data.return_value = self.valid_df
        
        result = self.engine.get_stock_data("AAPL")
        
        # التأكد من الحصول على DataFrame
        pd.testing.assert_frame_equal(result, self.valid_df)
        self.mock_p1.fetch_stock_data.assert_called_once()
        self.mock_p2.fetch_stock_data.assert_called_once()

    def test_cache_functionality(self):
        """اختبار عمل الكاش مع الـ DataFrame"""
        self.mock_p1.fetch_stock_data.return_value = self.valid_df
        
        # الطلب الأول: جلب من الـ Provider
        self.engine.get_stock_data("AAPL")
        # الطلب الثاني: جلب من الكاش
        result = self.engine.get_stock_data("AAPL")
        
        pd.testing.assert_frame_equal(result, self.valid_df)
        # التأكد أن الـ Provider لم يُستدعَ سوى مرة واحدة
        self.assertEqual(self.mock_p1.fetch_stock_data.call_count, 1)

if __name__ == '__main__':
    unittest.main()

    