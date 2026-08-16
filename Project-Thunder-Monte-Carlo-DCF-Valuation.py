import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================================
# 1. 基礎財務參數設定 (完全對齊 Excel 簡化版與真實歷史波動)
# =====================================================================
current_revenue = 1252.20183    # 2025A 精確基準營收 (1364.90 / 1.09)
ebit_margin = 0.0476885         # 精確 EBIT Margin (65.09 / 1364.90)
tax_rate = 0.15                 # 稅率 15%
wacc = 0.129                    # WACC 12.9%
perpetual_growth = 0.028        # 永續成長率 2.8%
projection_years = 5

actual_2025_wc = 409.0          # 2025A working capital
nwc_sales_ratio = 0.286         # WC % of revenue 28.6%

# 年中折現期數 (Mid-Year Convention: 0.5, 1.5, 2.5, 3.5, 4.5)
year_fractions = np.array([0.5, 1.5, 2.5, 3.5, 4.5])
discount_factors = 1 / ((1 + wacc) ** year_fractions)

# =====================================================================
# 2. 蒙地卡羅隨機參數設定
# =====================================================================
mean_growth = 0.09              # 期望成長率 9.0%
std_growth = 0.1677             # 基於歷史 3 年 (20.43%, -8.04%, 21.56%) 之樣本標準差
num_simulations = 10000

simulated_pv_fcf = []
simulated_pv_tv = []
simulated_ev = []

np.random.seed(42)  

for _ in range(num_simulations):
    # 隨機抽樣 5 年成長率 (含負成長情境)
    growths = np.random.normal(mean_growth, std_growth, projection_years)
    
    # 1. 營收預測
    revs = []
    temp_rev = current_revenue
    for g in growths:
        temp_rev *= (1 + g)
        revs.append(temp_rev)
        
    # 2. NOPAT 計算
    ebit = [r * ebit_margin for r in revs]
    nopat = [e * (1 - tax_rate) for e in ebit]
    
    # 3. NWC 變動計算 (衰退時會自動釋放營運資金)
    nwc_changes = []
    prior_wc = actual_2025_wc
    for r in revs:
        current_wc = r * nwc_sales_ratio
        nwc_changes.append(current_wc - prior_wc)
        prior_wc = current_wc
        
    # 4. FCFF 與年中折現 (前 5 年 FCF 現值)
    fcff = [nopat[i] - nwc_changes[i] for i in range(projection_years)]
    pv_fcff_sum = sum([fcff[i] * discount_factors[i] for i in range(projection_years)])
    
    # 5. 終值計算 (Terminal Value & PV of TV)
    terminal_rev = revs[-1] * (1 + perpetual_growth)
    terminal_nopat = (terminal_rev * ebit_margin) * (1 - tax_rate)
    terminal_nwc_change = (terminal_rev - revs[-1]) * nwc_sales_ratio
    terminal_fcff = terminal_nopat - terminal_nwc_change
    
    terminal_value = terminal_fcff / (wacc - perpetual_growth)
    pv_terminal_value = terminal_value * discount_factors[-1]
    
    # 6. 總企業價值 (Enterprise Value)
    ev = pv_fcff_sum + pv_terminal_value
    
    simulated_pv_fcf.append(pv_fcff_sum)
    simulated_pv_tv.append(pv_terminal_value)
    simulated_ev.append(ev)

simulated_pv_fcf = np.array(simulated_pv_fcf)
simulated_pv_tv = np.array(simulated_pv_tv)
simulated_ev = np.array(simulated_ev)

# =====================================================================
# 3. 統計數據輸出 (PV of Forecast + PV of TV = EV)
# =====================================================================
med_pv_fcf = np.median(simulated_pv_fcf)
med_pv_tv = np.median(simulated_pv_tv)
med_ev = np.median(simulated_ev)

p5_ev = np.percentile(simulated_ev, 5)
p95_ev = np.percentile(simulated_ev, 95)
static_base_ev = 522.17  # Excel 確定性基準點

print("=" * 65)
print("  Project Thunder - 蒙地卡羅 DCF 估值拆解與統計成果 (USD in Millions)")
print("=" * 65)
print(f" 前 5 年現金流現值中位數 (PV of FCF 2026-2030) : {med_pv_fcf:8.2f} USD")
print(f" 終值現值中位數         (PV of Terminal Value) : {med_pv_tv:8.2f} USD")
print("-" * 65)
print(f" 企業價值中位數         (Enterprise Value, EV) : {med_ev:8.2f} USD  (等於 {med_pv_fcf:.2f} + {med_pv_tv:.2f})")
print("=" * 65)
print(f" [風險區間對比]")
print(f" - Excel 靜態基準點 (Base EV, Std=0) : {static_base_ev:8.2f} USD")
print(f" - 5%  下行風險極限 (P5 Downside EV) : {p5_ev:8.2f} USD")
print(f" - 95% 上行潛力極限 (P95 Upside EV)  : {p95_ev:8.2f} USD")
print("=" * 65)

# =====================================================================
# 4. 繪製估值分佈與拆解圖表
# =====================================================================

plt.figure(figsize=(11, 6), dpi=100)

# 繪製 EV 直方圖
plt.hist(simulated_ev, bins=80, color='#2b5c8f', alpha=0.75, edgecolor='black', linewidth=0.5)

# 標示關鍵統計點位
plt.axvline(med_ev, color='#e74c3c', linestyle='-', linewidth=2.5, label=f'Median EV: ${med_ev:.1f}M')
plt.axvline(static_base_ev, color='#f39c12', linestyle='--', linewidth=2, label=f'Excel Base EV: ${static_base_ev:.1f}M')
plt.axvline(p5_ev, color='#27ae60', linestyle=':', linewidth=2, label=f'P5 Downside: ${p5_ev:.1f}M')
plt.axvline(p95_ev, color='#27ae60', linestyle=':', linewidth=2, label=f'P95 Upside: ${p95_ev:.1f}M')

# 主標題 (大字體 14pt + 加粗)
plt.suptitle('Project Thunder: Monte Carlo DCF Valuation', fontsize=14, fontweight='bold', y=0.98)

# 副標題 (小字體 10.5pt)
plt.title('(Stochastic Enterprise Value distribution Driven by Sales Growth Uncertainty)', fontsize=12, pad=12)

plt.xlabel('Enterprise Value (USD in Millions)', fontsize=11, labelpad=10)
plt.ylabel('Frequency (out of 10,000 simulations)', fontsize=11, labelpad=10)
plt.grid(axis='y', alpha=0.3, linestyle='--')

# 放置 PV 拆解數據框 (Valuation Component Breakdown Box)
box_text = (
    f"Valuation Component Breakdown\n"
    f"• PV of FCF (2026-2030) : ${med_pv_fcf:6.1f}M ({med_pv_fcf/med_ev*100:.1f}%)\n"
    f"• PV of Term Value     : ${med_pv_tv:6.1f}M ({med_pv_tv/med_ev*100:.1f}%)\n"
    f"-----------------------------------------\n"
    f"  Total Enterprise Value: ${med_ev:6.1f}M (100.0%)"
)
plt.gca().text(0.58, 0.65, box_text, transform=plt.gca().transAxes, fontsize=10,
               fontfamily='monospace', verticalalignment='top',
               bbox=dict(boxstyle='round,pad=0.8', facecolor='#f8f9fa', edgecolor='#bdc3c7', alpha=0.9))

plt.legend(loc='upper right', fontsize=10, framealpha=0.9)
plt.tight_layout()
plt.show()