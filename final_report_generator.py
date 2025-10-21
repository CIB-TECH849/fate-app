# -*- coding: utf-8 -*-
import datetime
from typing import List, Tuple, Dict

# =============================================================================
# Section 1: Data Definitions (User-Confirmed)
# =============================================================================

HEXAGRAM_MAP = {
    (1, 1, 1, 1, 1, 1): "乾為天", (0, 0, 0, 0, 0, 0): "坤為地", (1, 0, 0, 0, 1, 0): "水雷屯",
    (0, 1, 0, 0, 0, 1): "山水蒙", (1, 1, 1, 0, 1, 0): "水天需", (0, 1, 0, 1, 1, 1): "天水訟",
    (0, 1, 0, 0, 0, 0): "地水師", (0, 0, 0, 0, 1, 0): "水地比", (1, 1, 1, 0, 1, 1): "風天小畜",
    (0, 1, 1, 1, 1, 1): "天澤履", (1, 1, 1, 0, 0, 0): "地天泰", (0, 0, 0, 1, 1, 1): "天地否",
    (1, 0, 1, 1, 1, 1): "天火同人", (1, 1, 1, 1, 0, 1): "火天大有", (1, 0, 0, 0, 0, 0): "地山謙",
    (0, 0, 0, 1, 0, 0): "雷地豫", (0, 0, 1, 0, 1, 1): "澤雷隨", (1, 1, 0, 1, 0, 0): "雷澤歸妹",
    (0, 1, 1, 0, 0, 0): "地澤臨", (0, 0, 0, 1, 1, 0): "風地觀", (1, 0, 0, 1, 0, 1): "火雷噬嗑",
    (1, 0, 1, 0, 0, 1): "山火賁", (0, 0, 0, 1, 0, 0): "山地剝", (1, 0, 0, 0, 0, 0): "地雷復",
    (0, 0, 1, 1, 1, 1): "天雷無妄", (1, 1, 1, 1, 0, 0): "山天大畜", (1, 0, 0, 0, 0, 1): "山雷頤",
    (0, 1, 1, 1, 1, 0): "澤風大過", (0, 1, 0, 0, 1, 0): "坎為水", (1, 0, 1, 1, 0, 1): "離為火",
    (1, 0, 0, 0, 1, 1): "澤山咸", (1, 1, 0, 0, 0, 1): "雷風恆", (1, 0, 0, 1, 1, 1): "天山遁",
    (1, 1, 1, 0, 0, 1): "雷天大壯", (0, 0, 0, 1, 0, 1): "火地晉", (1, 0, 1, 0, 0, 0): "地火明夷",
    (1, 0, 1, 1, 1, 0): "風火家人", (0, 1, 1, 1, 0, 1): "火澤睽", (1, 0, 0, 0, 1, 0): "水山蹇",
    (0, 1, 0, 0, 0, 1): "雷水解", (0, 1, 1, 1, 0, 0): "山澤損", (0, 0, 1, 1, 1, 0): "風雷益",
    (0, 1, 1, 1, 1, 1): "澤天夬", (1, 1, 1, 1, 1, 0): "天風姤", (0, 0, 0, 0, 1, 1): "澤地萃",
    (1, 1, 0, 0, 0, 0): "地風升", (0, 1, 1, 0, 1, 0): "澤水困", (1, 1, 0, 0, 1, 0): "水風井",
    (1, 0, 1, 0, 1, 1): "澤火革", (1, 1, 0, 1, 0, 1): "火風鼎", (0, 0, 1, 0, 0, 1): "震為雷",
    (1, 0, 0, 1, 0, 0): "艮為山", (1, 0, 0, 1, 1, 0): "風山漸", (0, 1, 1, 0, 0, 1): "山風蠱",
    (1, 0, 1, 1, 0, 0): "雷火豐", (0, 0, 1, 1, 0, 1): "火山旅", (1, 1, 0, 1, 1, 0): "巽為風",
    (0, 1, 1, 0, 1, 1): "兌為澤", (0, 1, 0, 1, 1, 0): "風水渙", (0, 1, 0, 0, 1, 1): "水澤節",
    (0, 1, 1, 1, 1, 0): "風澤中孚", (0, 0, 1, 1, 0, 0): "雷山小過", (1, 0, 1, 0, 1, 0): "水火既濟",
    (0, 1, 0, 1, 0, 1): "火水未濟"
}
NAME_TO_STRUCTURE = {v: k for k, v in HEXAGRAM_MAP.items()}
PALACE_DATA = {
    "乾": ["乾為天", "天風姤", "天山遁", "天地否", "風地觀", "山地剝", "火地晉", "火天大有"],
    "坎": ["坎為水", "水澤節", "水雷屯", "水火既濟", "澤火革", "雷火豐", "地火明夷", "地水師"],
    "艮": ["艮為山", "山火賁", "山天大畜", "山澤損", "火澤睽", "天澤履", "風澤中孚", "風山漸"],
    "震": ["震為雷", "雷地豫", "雷水解", "雷風恆", "地風升", "水風井", "澤風大過", "澤雷隨"],
    "巽": ["巽為風", "風天小畜", "風火家人", "風雷益", "天雷無妄", "火雷噬嗑", "山雷頤", "山風蠱"],
    "離": ["離為火", "火山旅", "火風鼎", "火水未濟", "山水蒙", "風水渙", "天水訟", "天火同人"],
    "兌": ["兌為澤", "澤水困", "澤地萃", "澤山咸", "水山蹇", "地山謙", "雷山小過", "雷澤歸妹"],
    "坤": ["坤為地", "地雷復", "地澤臨", "地天泰", "雷天大壯", "澤天夬", "水天需", "水地比"]
}
GENERATION_NAMES = ["本宮卦", "一世卦", "二世卦", "三世卦", "四世卦", "五世卦", "游魂卦", "歸魂卦"]
HEXAGRAM_COMPOSITION = {
    "乾為天": ("乾", "乾"), "坤為地": ("坤", "坤"), "水雷屯": ("震", "坎"), "山水蒙": ("坎", "艮"),
    "水天需": ("乾", "坎"), "天水訟": ("坎", "乾"), "地水師": ("坎", "坤"), "水地比": ("坤", "坎"),
    "風天小畜": ("乾", "巽"), "天澤履": ("兌", "乾"), "地天泰": ("乾", "坤"), "天地否": ("坤", "乾"),
    "天火同人": ("離", "乾"), "火天大有": ("乾", "離"), "地山謙": ("艮", "坤"), "雷地豫": ("坤", "震"),
    "澤雷隨": ("震", "兌"), "山風蠱": ("巽", "艮"), "地澤臨": ("兌", "坤"), "風地觀": ("坤", "巽"),
    "火雷噬嗑": ("震", "離"), "山火賁": ("離", "艮"), "山地剝": ("艮", "坤"), "地雷復": ("震", "坤"),
    "天雷無妄": ("震", "乾"), "山天大畜": ("乾", "艮"), "山雷頤": ("震", "艮"), "澤風大過": ("巽", "兌"),
    "坎為水": ("坎", "坎"), "離為火": ("離", "離"), "澤山咸": ("艮", "兌"), "雷風恆": ("巽", "震"),
    "天山遁": ("艮", "乾"), "雷天大壯": ("乾", "震"), "火地晉": ("坤", "離"), "地火明夷": ("離", "坤"),
    "風火家人": ("離", "巽"), "火澤睽": ("兌", "離"), "水山蹇": ("艮", "坎"), "雷水解": ("坎", "震"),
    "山澤損": ("兌", "艮"), "風雷益": ("震", "巽"), "澤天夬": ("乾", "兌"), "天風姤": ("巽", "乾"),
    "澤地萃": ("坤", "兌"), "地風升": ("巽", "坤"), "澤水困": ("坎", "兌"), "水風井": ("巽", "坎"),
    "澤火革": ("離", "兌"), "火風鼎": ("巽", "離"), "震為雷": ("震", "震"), "艮為山": ("艮", "艮"),
    "風山漸": ("艮", "巽"), "雷澤歸妹": ("兌", "震"), "雷火豐": ("離", "震"), "火山旅": ("艮", "離"),
    "巽為風": ("巽", "巽"), "兌為澤": ("兌", "兌"), "風水渙": ("坎", "巽"), "水澤節": ("兌", "坎"),
    "風澤中孚": ("兌", "巽"), "雷山小過": ("艮", "震"), "水火既濟": ("離", "坎"), "火水未濟": ("坎", "離")
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
PALACE_ELEMENTS = {
    '乾': '金', '兌': '金', '離': '火', '震': '木',
    '巽': '木', '坎': '水', '艮': '土', '坤': '土'
}
SIX_GODS = ['青龍', '朱雀', '勾陳', '螣蛇', '白虎', '玄武']
SIX_GODS_START_INDEX = {
    '甲': 0, '乙': 0, '丙': 1, '丁': 1, '戊': 2, '己': 3, '庚': 4, '辛': 4, '壬': 5, '癸': 5
}

def get_hexagram_from_lines(lines: Tuple[int, ...]) -> str:
    return HEXAGRAM_MAP.get(lines, "未知卦")

def get_changed_hexagram_name(original_hex_name, moving_lines):
    original_structure = NAME_TO_STRUCTURE.get(original_hex_name)
    if not original_structure: return "未知卦"
    changed_structure = list(original_structure)
    for line_num in moving_lines:
        if 1 <= line_num <= 6:
            changed_structure[line_num - 1] = 1 - changed_structure[line_num - 1]
    return get_hexagram_from_lines(tuple(changed_structure))

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

def analyze_hexagram(hex_name, day_stem, day_element):
    if hex_name not in HEXAGRAM_COMPOSITION: return None, f"錯誤：找不到卦名 '{hex_name}' 的組成規則。"
    structure = NAME_TO_STRUCTURE.get(hex_name)
    if not structure: return None, f"錯誤：在爻象結構圖中找不到 '{hex_name}'。"
    upper_trigram, lower_trigram = HEXAGRAM_COMPOSITION[hex_name]
    palace_trigram = [p for p, h_list in PALACE_DATA.items() if hex_name in h_list][0]
    palace_element = PALACE_ELEMENTS[palace_trigram]
    analysis_result = {
        "hex_name": hex_name, "palace_name": palace_trigram, "palace_element": palace_element,
        "day_stem": day_stem, "day_element": day_element, "lines": []
    }
    lower_stem, _, lower_branches, _ = NA_JIA_RULES[lower_trigram]
    _, upper_stem, _, upper_branches = NA_JIA_RULES[upper_trigram]
    stems = [lower_stem[0]] * 3 + [upper_stem[0]] * 3
    branches = lower_branches + upper_branches
    line_positions = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']
    start_god_index = SIX_GODS_START_INDEX[day_stem]
    for i in range(6):
        branch = branches[i]
        line_element = BRANCH_ELEMENTS[branch]
        six_relative = get_six_relatives(line_element, day_element)
        six_god = SIX_GODS[(start_god_index + i) % 6]
        analysis_result["lines"].append({
            "position": line_positions[i], "yin_yang": structure[i], "stem": stems[i], "branch": branch,
            "element": line_element, "relative": six_relative, "six_god": six_god
        })
    return analysis_result, None

def display_full_analysis(main_analysis, changed_analysis, moving_lines):
    if not main_analysis: return
    print(f"--- 主卦分析：【{main_analysis['hex_name']}】 ---")
    gen_name_list = [gn for p, h_list in PALACE_DATA.items() if main_analysis['hex_name'] in h_list for gn in GENERATION_NAMES if h_list.index(main_analysis['hex_name']) == GENERATION_NAMES.index(gn)]
    gen_name = gen_name_list[0] if gen_name_list else '未知'
    print(f"  - 本卦屬性： {main_analysis['palace_name']}宮{gen_name} (五行：{main_analysis['palace_element']})\n")
    print(f"  {'爻位':<4}{'陰陽':<3}{ '動':<2}{ '六神':<4}{ '納甲':<6}{ '地支':<4}{ '五行':<4}{ '六親':<5}")
    print(f"  {'-'*4:<4}{'-'*3:<3}{'-'*2:<2}{'-'*4:<4}{'-'*6:<6}{'-'*4:<4}{'-'*4:<4}{'-'*5:<5}")
    for i, line in enumerate(reversed(main_analysis["lines"])):
        line_num = 6 - i
        moving_marker = "●" if line_num in moving_lines else ""
        full_stem_branch = f'{line["stem"]}{line["branch"]}'
        yin_yang_symbol = "—" if line['yin_yang'] == 1 else "--"
        print(f"  {line['position']:<4}{yin_yang_symbol:<3}{moving_marker:<2}{line['six_god']:<4}{full_stem_branch:<6}{line["branch"]:<4}{line["element"]:<4}{line["relative"]:<5}")
    print("\n")

    if changed_analysis:
        print(f"--- 變卦分析：【{changed_analysis['hex_name']}】 ---")
        print("  動爻變為：")
        for line_num in moving_lines:
            original_line = main_analysis["lines"][line_num - 1]
            changed_line = changed_analysis["lines"][line_num - 1]
            print(f"    {original_line['position']} {original_line['relative']} {original_line['branch']} -> {changed_line['relative']} {changed_line['branch']}")
    print("\n" + "-"*40 + "\n")

if __name__ == "__main__":
    # Hardcoded inputs for the final report
    hex_name = "雷澤歸妹"
    day_stem = "戊"
    day_element = "土"
    moving_lines = [3]

    # Perform analysis
    main_analysis, error = analyze_hexagram(hex_name, day_stem, day_element)
    changed_analysis = None
    if moving_lines:
        changed_hex_name = get_changed_hexagram_name(hex_name, moving_lines)
        if changed_hex_name != "未知卦":
            changed_analysis, _ = analyze_hexagram(changed_hex_name, day_stem, day_element)
    
    # Display Report
    display_full_analysis(main_analysis, changed_analysis, moving_lines)
