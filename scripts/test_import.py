import sys
sys.path.append('.')
import market_analysis_v3 as ma
print("Import successful")
res = ma.run_analysis("NIFTY")
print(res[4], res[5])
