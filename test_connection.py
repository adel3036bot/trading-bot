from market.data_engine import (
    get_stock_data,
    get_vix_data,
    get_option_chain_data
)

print("===================================")
print("ADEL SMART BOT - CONNECTION TEST")
print("===================================")

# ===========================
# STOCK TEST
# ===========================
print("\nجاري جلب بيانات SPY...")

spy_data = get_stock_data("SPY")

if spy_data is not None:
    print("✅ نجح جلب SPY")
    print(spy_data)
else:
    print("❌ فشل جلب SPY")

# ===========================
# VIX TEST
# ===========================
print("\nجاري جلب بيانات VIX...")

vix_data = get_vix_data()

if vix_data is not None:
    print("✅ نجح جلب VIX")
    print(vix_data)
else:
    print("❌ فشل جلب VIX")

# ===========================
# OPTION CHAIN TEST
# ===========================
print("\nجاري جلب Option Chain...")

option_data = get_option_chain_data("SPY")

if option_data is not None:
    print("✅ نجح جلب Option Chain")
    print(type(option_data))
else:
    print("❌ فشل جلب Option Chain")

print("\n===================================")
print("TEST FINISHED")
print("===================================")

