# -*- coding: utf-8 -*-

# =============================================================================
# Section 1: Data Definitions (from liuyao_system.py)
# =============================================================================

PALACE_DATA = {
    "乾": ["乾", "姤", "遯", "否", "觀", "剝", "晉", "大有"], "震": ["震", "豫", "解", "恒", "升", "井", "大過", "隨"],
    "坎": ["坎", "節", "屯", "既濟", "革", "豐", "明夷", "師"], "艮": ["艮", "賁", "大畜", "損", "睽", "履", "中孚", "漸"],
    "坤": ["坤", "復", "臨", "泰", "大壯", "夬", "需", "比"], "巽": ["巽", "小畜", "家人", "益", "无妄", "噬嗑", "頤", "蠱"],
    "離": ["離", "旅", "鼎", "未濟", "蒙", "渙", "訟", "同人"], "兌": ["兌", "困", "萃", "咸", "蹇", "謙", "小過", "歸妹"]
}
GENERATION_NAMES = ["本宮卦", "一世卦", "二世卦", "三世卦", "四世卦", "五世卦", "游魂卦", "歸魂卦"]
HEXAGRAM_COMPOSITION = {
    "乾": ("乾", "乾"), "坤": ("坤", "坤"), "屯": ("坎", "震"), "蒙": ("艮", "坎"),
    "需": ("坎", "乾"), "訟": ("乾", "坎"), "師": ("坤", "坎"), "比": ("坎", "坤"),
    "小畜": ("巽", "乾"), "履": ("乾", "兌"), "泰": ("坤", "乾"), "否": ("乾", "坤"),
    "同人": ("乾", "離"), "大有": ("離", "乾"), "謙": ("坤", "艮"), "豫": ("震", "坤"),
    "隨": ("兌", "震"), "蠱": ("艮", "巽"), "臨": ("坤", "兌"), "觀": ("巽", "坤"),
    "噬嗑": ("離", "震"), "賁": ("艮", "離"), "剝": ("艮", "坤"), "復": ("坤", "震"),
    "无妄": ("乾", "震"), "大畜": ("艮", "乾"), "頤": ("艮", "震"), "大過": ("兌", "巽"),
    "坎": ("坎", "坎"), "離": ("離", "離"), "咸": ("兌", "艮"), "恒": ("震", "巽"),
    "遯": ("乾", "艮"), "大壯": ("震", "乾"), "晉": ("離", "坤"), "明夷": ("坤", "離"),
    "家人": ("巽", "離"), "睽": ("離", "兌"), "蹇": ("坎", "艮"), "解": ("震", "坎"),
    "損": ("艮", "兌"), "益": ("巽", "震"), "夬": ("兌", "乾"), "姤": ("乾", "巽"),
    "萃": ("兌", "坤"), "升": ("坤", "巽"), "困": ("兌", "坎"), "井": ("坎", "巽"),
    "革": ("兌", "離"), "鼎": ("離", "巽"), "震": ("震", "震"), "艮": ("艮", "艮"),
    "漸": ("巽", "艮"), "歸妹": ("震", "兌"), "豐": ("震", "離"), "旅": ("離", "艮"),
    "巽": ("巽", "巽"), "兌": ("兌", "兌"), "渙": ("巽", "坎"), "節": ("坎", "兌"),
    "中孚": ("巽", "兌"), "小過": ("震", "艮"), "既濟": ("坎", "離"), "未濟": ("離", "坎")
}
NA_JIA_RULES = {
    "乾": (("甲"), ("壬"), ['子', '寅', '辰'], ['午', '申', '戌']),
    "坤": (("乙"), ("癸"), ['未', '巳', '卯'], ['丑', '亥', '酉']),
    "震": (("庚"), ("庚"), ['子', '寅', '辰'], ['午', '申', '戌']),
    "巽": (("辛"), ("辛"), ['丑', '亥', '酉'], ['未', '巳', '卯']),
    "坎": (("戊"), ("戊"), ['寅', '辰', '午'], ['申', '戌', '子']),
    "離": (("己"), ("己"), ['卯', '丑', '亥'], ['酉', '未', '巳']),
    "艮": (("丙"), ("丙"), ['辰', '午', '申'], ['戌', '子', '寅']),
    "兌": (("丁"), ("丁"), ['巳', '卯', '丑'], ['亥', '酉', '未'])
}
BRANCH_ELEMENTS = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
    '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
}

# =============================================================================
# Section 2: Core Logic Functions
# =============================================================================

def get_six_relatives(line_element, day_master_element):
    if line_element == day_master_element: return '兄弟'
    relations = {
        '木': {'火': '子孫', '土': '妻財', '金': '官鬼', '水': '父母'},
        '火': {'土': '子孫', '金': '妻財', '水': '官鬼', '木': '父母'},
        '土': {'金': '子孫', '水': '妻財', '木': '官鬼', '火': '父母'},
        '金': {'水': '子孫', '木': '妻財', '火': '官鬼', '土': '父母'},
        '水': {'木': '子孫', '火': '妻財', '土': '官鬼', '金': '父母'}
    }
    return relations[day_master_element].get(line_element, '錯誤')

def analyze_hexagram(hex_name, day_master_element):
    if hex_name not in HEXAGRAM_COMPOSITION: return None
    upper_trigram, lower_trigram = HEXAGRAM_COMPOSITION[hex_name]
    analysis_lines = []
    lower_stem, _, lower_branches, _ = NA_JIA_RULES[lower_trigram]
    _, upper_stem, _, upper_branches = NA_JIA_RULES[upper_trigram]
    stems = [lower_stem[0]] * 3 + [upper_stem[0]] * 3
    branches = lower_branches + upper_branches
    for i in range(6):
        branch = branches[i]
        line_element = BRANCH_ELEMENTS[branch]
        six_relative = get_six_relatives(line_element, day_master_element)
        analysis_lines.append({
            "position": i + 1,
            "stem": stems[i],
            "branch": branch,
            "element": line_element,
            "relative": six_relative
        })
    return analysis_lines

# =============================================================================
# Section 3: Report Generation
# =============================================================================

def generate_report(hex_name, day_master_tuple, question):
    day_master_element = day_master_tuple[1]
    lines = analyze_hexagram(hex_name, day_master_element)
    if not lines:
        print(f"無法分析 {hex_name} 卦。請檢查卦名是否正確。")
        return

    day_master_stem = day_master_tuple[0]

    print("### 1. 系統分析設定")
    print(f"*   **卦象**：{hex_name}")
    print(f"*   **日干**：{day_master_stem} (五行屬 **{day_master_element}**)")
    print(f"*   **占事**：{question}\n")

    print("### 2. 乾卦的納甲與六親分析")
    print(f"系統採用了京房納甲法來配置乾卦的六爻，並以**日干「{day_master_stem}{day_master_element}」**為基準來裝配六親。\n")
    print("#### 六親裝配規則（日干：" + day_master_stem + day_master_element + "）")
    print("| 五行 (爻支) | 與日主「" + day_master_stem + day_master_element + "」的關係 | 六親名稱 |")
    print("| :------------ | :--------------------- | :------- |")
    print(f"| {day_master_element}            | 同我者（比和）         | 兄弟     |")
    print(f"| 金            | 我生者（土生金）       | 子孫     |")
    print(f"| 火            | 生我者（火生土）       | 父母     |")
    print(f"| 木            | 克我者（木克土）       | 官鬼     |")
    print(f"| 水            | 我克者（土克水）       | 妻財     |\n")

    print("#### 乾卦六爻分析結果")
    print("| 爻位 | 納甲（天干地支） | 地支 | 五行 | 六親 |")
    print("| :--- | :--------------- | :--- | :--- | :--- |")
    line_positions = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']
    target_relative_line = None
    target_relative_element = None
    for i, line in enumerate(lines):
        pos = line_positions[i]
        stem_branch = f'{line["stem"]}{line["branch"]}'
        is_target = ""
        if line["relative"] == "官鬼":
            target_relative_line = f'{pos} {stem_branch} {line["element"]}'
            target_relative_element = line["element"]
            is_target = "**"
        
        # Corrected line reversal logic for printing
        print_pos = line_positions[line["position"]-1]
        print(f"| {print_pos} | {stem_branch} | {line["branch"]}   | {line["element"]}   | {is_target}{line["relative"]}{is_target} |")

    # Re-find the target line details after the loop for clarity
    for line in lines:
        if line["relative"] == "官鬼":
            pos = line_positions[line["position"]-1]
            stem_branch = f'{line["stem"]}{line["branch"]}'
            target_relative_line = f'{pos} {stem_branch} {line["element"]}'
            target_relative_element = line["element"]
            break

    print("\n")

    print("### 3. 占事指引")
    print(f"*   **占事類別**： {question}")
    print("*   **核心用神（目標爻）**： **官鬼爻**")
    print("*   **說明**： 在六爻斷卦中，問事業、工作、功名通常以「官鬼爻」為用神，代表事業、職位、壓力或阻礙。\n")
    print("#### 目標爻詳情：")
    if target_relative_line:
        print(f"*   **{target_relative_line}**\n")
    else:
        print("*   此卦中未找到官鬼爻。\n")

    print("### 結論與下一步分析方向")
    print("系統已經成功完成了基礎的納甲和六親裝配步驟，並找出了問「事業」的核心用神。")
    print("接下來的完整分析通常會包括：\n")
    print(f"1.  **分析用神（官鬼爻）的旺衰**： 考慮日辰（{day_master_stem}{day_master_element}）、月建（未給出，需補充）對用神（{target_relative_element}）的生克關係，判斷事業的吉凶或進展順利與否。")
    print("2.  **分析世爻與應爻**： 判斷問事者（世爻）與問事對象（應爻）的狀態和關係。")
    print("3.  **分析動爻/變爻**（此處未顯示動爻）： 如果卦中有爻變動，則需要分析變爻對用神的影響。")
    print(f"4.  **綜合判斷**： 結合卦象、宮位（乾宮屬金，對{target_relative_element}有克制作用）、六神（未顯示）等進行詳細的吉凶和時間判斷。")

if __name__ == "__main__":
    hex_to_analyze = "乾"
    day_master_input = ("戊", "土")
    question_to_ask = "事業"
    generate_report(hex_to_analyze, day_master_input, question_to_ask)
