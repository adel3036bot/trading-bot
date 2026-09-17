"""Stock universe eligibility only.  It never creates a trading signal."""
from __future__ import annotations
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed


class UniverseEngine:
    # Initial candidates, intentionally configurable rather than production claims.
    def __init__(self, reference_source, quote_source=None, *, min_price=1.50, max_workers=8):
        self.reference_source, self.quote_source = reference_source, quote_source
        self.min_price, self.max_workers = min_price, max_workers
        self.cache, self.rejections = {}, Counter()

    def eligible(self, item):
        if not item.get("active", False): return "inactive"
        if str(item.get("market", "stocks")).lower() != "stocks": return "non_stock_market"
        if str(item.get("type", "CS")).upper() not in {"CS", "COMMON_STOCK"}: return "non_common_stock"
        if not item.get("ticker") or not item.get("primary_exchange"): return "missing_classification"
        return None

    def scan(self, limit_pages=None):
        raw = list(self.reference_source.iter_us_stocks(max_pages=limit_pages))
        eligible = [x for x in raw if not self.eligible(x)]
        for x in raw:
            reason=self.eligible(x)
            if reason:self.rejections[reason]+=1
        qualified=[]
        if not self.quote_source: return {"raw":len(raw),"eligible":eligible,"qualified":qualified,"rejections":dict(self.rejections),"requests":0}
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            futures={pool.submit(self.quote_source.get_quote, x["ticker"]):x for x in eligible}
            for future in as_completed(futures):
                item=futures[future]
                try: quote=future.result()
                except Exception: self.rejections["quote_failure"]+=1; continue
                price=(quote or {}).get("last")
                if (quote or {}).get("data_quality") not in ("VERIFIED", "REALTIME"):
                    self.rejections["quote_not_verified_realtime"]+=1
                elif not isinstance(price,(int,float)): self.rejections["no_reliable_quote"]+=1
                elif price < self.min_price:self.rejections["price_below_1_50"]+=1
                else: qualified.append({**item,"quote":quote})
        return {"raw":len(raw),"eligible":eligible,"qualified":qualified,"rejections":dict(self.rejections),"requests":len(eligible)}
