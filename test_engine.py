# محاولة استيراد الدالة مباشرة لتجنب أي مشاكل في مسار المجلدات
try:
    from market.data_engine import get_stock_data
    print("🧪 TESTING DATA ENGINE...")
    data = get_stock_data("NVDA")
    
    if data:
        print("✅ SUCCESS! Data received:")
        print(data)
    else:
        print("❌ FAILED! No data returned. Please check the logs in the terminal.")
        
except ModuleNotFoundError:
    print("⚠️ ModuleNotFoundError: تأكد أن مجلد 'market' يحتوي على ملف __init__.py")
except Exception as e:
    print(f"❌ ERROR DURING TEST: {e}")

    