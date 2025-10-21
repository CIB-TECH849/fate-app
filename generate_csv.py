# -*- coding: utf-8 -*-
import csv
import os

# =============================================================================
# Section 1: Data Definitions (from liuyao_system.py)
# =============================================================================

PALACE_DATA = {
    "乾": ["乾", "姤", "遯", "否", "觀", "剝", "晉", "大有"], "震": ["震", "豫", "解", "恒", "升", "井", "大過", "隨"],
    "坎": ["坎", "節", "屯", "既濟", "革", "豐", "明夷", "師"], "艮": ["艮", "賁", "大畜", "損", "睽", "履", "中孚", "漸"],
    "坤": ["坤", "復", "臨", "泰", "大壯", "夬", "需", "比"], "巽": ["巽", "小畜", "家人", "益", "无妄", "噬嗑", "頤", "蠱"],
    "離": ["離", "旅", "鼎", "未濟", "蒙", "渙", "訟", "同人"], "兌": ["兌", "困", "萃", "咸", "蹇", "謙", "小過", "歸妹"]
}

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

HEXAGRAM_ORDER = [
    "乾","坤","屯","蒙","需","訟","師","比","小畜","履","泰","否","同人","大有","謙","豫",
    "隨","蠱","臨","觀","噬嗑","賁","剝","復","无妄","大畜","頤","大過","坎","離","咸","恒",
    "遯","大壯","晉","明夷","家人","睽","蹇","解","損","益","夬","姤","萃","升","困","井",
    "革","鼎","震","艮","漸","歸妹","豐","旅","巽","兌","渙","節","中孚","小過","既濟","未濟"
]

# =============================================================================
# Section 2: Core Logic Functions (from liuyao_system.py)
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

def get_full_analysis(hex_name, day_master_element):
    if hex_name not in HEXAGRAM_COMPOSITION: return None, None
    upper_trigram, lower_trigram = HEXAGRAM_COMPOSITION[hex_name]
    
    # Find the palace of the hexagram
    palace_trigram = None
    for p, h_list in PALACE_DATA.items():
        if hex_name in h_list:
            palace_trigram = p
            break
    if not palace_trigram: return None, None # Should not happen with full data

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
            "line_num": i + 1,
            "stem": stems[i],
            "branch": branch,
            "element": line_element,
            "relative": six_relative
        })
    return palace_trigram, analysis_lines

# =============================================================================
# Section 3: CSV Generation
# =============================================================================

def generate_csv():
    day_master_element = '木' # As specified: 假設日干為甲（甲木）
    file_path = os.path.join("C:\\fate2", "64卦_京房納甲_日干甲示例.csv")

    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["HexIndex", "HexName", "Palace", "LineNum(1=bottom)", "Stem", "Branch", "Element", f"SixRel(日干={day_master_element})"])
        
        for idx, hex_name in enumerate(HEXAGRAM_ORDER):
            palace, lines = get_full_analysis(hex_name, day_master_element)
            if not lines:
                # Write a placeholder row if analysis fails for some reason
                writer.writerow([idx + 1, hex_name, "未知", 0, "", "", "", ""])
                continue
            
            for line_data in lines:
                writer.writerow([
                    idx + 1,
                    hex_name,
                    palace,
                    line_data["line_num"],
                    line_data["stem"],
                    line_data["branch"],
                    line_data["element"],
                    line_data["relative"]
                ])
    print(f"[完成] 已建立 CSV 檔案於：{file_path}")

if __name__ == "__main__":
    generate_csv()
