# test_meihua.py

import gemini_meihua_module as meihua
import json

# --- 測試案例 1：澤火革，第五爻動 ---
print("--- 測試案例 1：澤火革，第五爻動 ---")
lines_for_ge = [1, 0, 1, 0, 1, 1] # 澤火革的六爻
moving_line_ge = 5 # 第五爻為動爻

print(f"正在查詢六爻為 {lines_for_ge}，動爻為 {moving_line_ge} 的卦象...")
interpretation_ge = meihua.interpret_hexagrams_from_lines(lines_for_ge, moving_line_ge)

print("\n--- 查詢結果 ---")
print(json.dumps(interpretation_ge, ensure_ascii=False, indent=4))

# --- 測試案例 2：乾為天，無動爻 ---
print("\n\n--- 測試案例 2：乾為天，無動爻 ---")
lines_for_qian = [1, 1, 1, 1, 1, 1] # 乾為天的六爻

print(f"正在查詢六爻為 {lines_for_qian} 的卦象...")
interpretation_qian = meihua.interpret_hexagrams_from_lines(lines_for_qian)

print("\n--- 查詢結果 ---")
print(json.dumps(interpretation_qian, ensure_ascii=False, indent=4))