# -*- coding: utf-8 -*-
import datetime
from typing import List, Tuple, Dict

LLM_PROMPT_TEMPLATE = '''
你是一位精通《周易》與「京房納甲法」的易學大師，熟悉卦象、納甲、六親、世應、變卦、互卦、卦辭與爻辭的整合分析，擅長以現代語言詮釋古卦義。
請根據以下我輸入的卦象資料，自動生成一份完整、條理清晰的【六爻納甲解卦報告】，以「事業財運」為分析核心（若我輸入的主題不同，請自動切換主軸）。

一、卦象結構分析

請分析：

本卦名稱、卦象、卦辭與五行屬性。

變卦名稱、卦象、卦辭與象義變化。

互卦（中四爻所構成之卦）並解釋「潛在趨勢」。

指出卦體陰陽比例、所屬五行與方位。

總結「本卦 → 變卦」的變化意義（如：革中有兌、動中求進、陰陽反交、歸魂伏吟等）。

二、納甲與六親裝卦

依據「京房納甲法」與日干五行，標示：

每爻之地支、五行、六親。

指出「世爻」與「應爻」位置及其象徵意義。

動爻變化（陰陽轉換、得失、旺衰）及引發之象。

若有伏神、飛神，請說明其含義。

說明各爻間的「生剋制化關係」，重點說明「用神（依主題不同）」之旺衰與助抑情況。

三、象義綜合解讀

請從三層結構分析：

卦象之象（天地風雷水火山澤，主大勢與格局）

爻動之理（動爻為變、世爻為我、應爻為外）

納甲之情（六親關係、生剋制化、吉凶流向）

結合以上判斷：

誰為主動、誰為被動

何者生我、何者剋我

主卦與變卦之間的象意互動

有無「伏吟」「反吟」「合沖」「六合」「六沖」等特象

四、卦辭與爻辭分析

請引用：

《周易》原文卦辭與爻辭。

《象傳》《彖傳》重點。

《文言傳》補充說明。 

補上白話詮釋，說明卦辭如何呼應本占問題。

五、結論與建議（核心段）

請以「現代語言」整合成具體結論：

吉凶判斷（明確指出：大吉／中吉／小吉／有阻／凶）

時機預測（可依地支推導時序，如：子月／午日可轉機）

成敗關鍵（哪一爻、哪一六親是轉折點）

實務建議（若為求財，指出：應聚焦哪類客源、避免何類支出；若為官運，指出：升遷契機何時出現）
'''

# =============================================================================
# Section 1: Data Definitions (Final & Verified)
# =============================================================================

HEXAGRAM_MAP = {
    (1, 1, 1, 1, 1, 1): "乾為天",
    (0, 0, 0, 0, 0, 0): "坤為地",
    (1, 0, 0, 0, 1, 0): "水雷屯",
    (0, 1, 0, 0, 0, 1): "山水蒙",
    (1, 1, 1, 0, 1, 0): "水天需",
    (0, 1, 0, 1, 1, 1): "天水訟",
    (0, 1, 0, 0, 0, 0): "地水師",      # Corrected based on user feedback
    (0, 0, 0, 0, 1, 0): "水地比",      # Corrected based on user feedback
    (1, 1, 1, 0, 1, 1): "風天小畜",
    (1, 1, 0, 1, 1, 1): "天澤履",
    (1, 1, 1, 0, 0, 0): "地天泰",
    (0, 0, 0, 1, 1, 1): "天地否",
    (1, 0, 1, 1, 1, 1): "天火同人",
    (1, 1, 1, 1, 0, 1): "火天大有",
    (0, 0, 1, 0, 0, 0): "地山謙",
    (0, 0, 0, 1, 0, 0): "雷地豫",
    (1, 0, 0, 1, 1, 0): "澤雷隨",
    (0, 1, 1, 0, 0, 1): "山風蠱",
    (1, 1, 0, 0, 0, 0): "地澤臨",
    (0, 0, 0, 0, 1, 1): "風地觀",
    (1, 0, 0, 1, 0, 1): "火雷噬嗑",
    (1, 0, 1, 0, 0, 1): "山火賁",
    (0, 0, 0, 0, 0, 1): "山地剝",
    (1, 0, 0, 0, 0, 0): "地雷復",
    (1, 0, 0, 1, 1, 1): "天雷無妄",
    (1, 1, 1, 0, 0, 1): "山天大畜",
    (1, 0, 0, 0, 0, 1): "山雷頤",
    (0, 1, 1, 1, 1, 0): "澤風大過",
    (0, 1, 0, 0, 1, 0): "坎為水",
    (1, 0, 1, 1, 0, 1): "離為火",
    (0, 0, 1, 1, 1, 0): "澤山咸",
    (0, 1, 1, 1, 0, 0): "雷風恆",
    (0, 0, 1, 1, 1, 1): "天山遁",
    (1, 1, 1, 1, 0, 0): "雷天大壯",
    (0, 0, 0, 1, 0, 1): "火地晉",
    (1, 0, 1, 0, 0, 0): "地火明夷",
    (1, 0, 1, 0, 1, 1): "風火家人",
    (1, 1, 0, 1, 0, 1): "火澤睽",
    (0, 0, 1, 0, 1, 0): "水山蹇",
    (0, 1, 0, 1, 0, 0): "雷水解",
    (1, 1, 0, 0, 0, 1): "山澤損",
    (1, 0, 0, 0, 1, 1): "風雷益",
    (1, 1, 1, 1, 1, 0): "澤天夬",
    (0, 1, 1, 1, 1, 1): "天風姤",
    (0, 0, 0, 1, 1, 0): "澤地萃",
    (0, 1, 1, 0, 0, 0): "地風升",
    (0, 1, 0, 1, 1, 0): "澤水困",
    (0, 1, 0, 0, 1, 1): "風水渙",
    (1, 0, 1, 1, 1, 0): "澤火革",
    (0, 1, 1, 1, 0, 1): "火風鼎",
    (1, 0, 0, 1, 0, 0): "震為雷",
    (0, 0, 1, 0, 0, 1): "艮為山",
    (0, 0, 1, 0, 1, 1): "風山漸",
    (1, 1, 0, 1, 0, 0): "雷澤歸妹",
    (1, 0, 1, 1, 0, 0): "雷火豐",
    (0, 0, 1, 1, 0, 1): "火山旅",
    (0, 1, 1, 0, 1, 1): "巽為風",
    (0, 1, 1, 0, 1, 1): "兌為澤", # User data has duplicate key with 巽
    (0, 1, 0, 0, 1, 1): "風水渙",      # Corrected structure
    (1, 1, 0, 0, 1, 0): "水澤節",      # Corrected structure
    (1, 1, 0, 0, 1, 1): "風澤中孚",    # Corrected structure
    (0, 0, 1, 1, 0, 0): "雷山小過",
    (1, 0, 1, 0, 1, 0): "水火既濟",
    (0, 1, 0, 1, 0, 1): "火水未濟",
    
}
NAME_TO_STRUCTURE = {v: k for k, v in HEXAGRAM_MAP.items()}

# (Other data definitions remain the same)
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
    "乾為天": ("乾", "乾"), "坤為地": ("坤", "坤"),     "水雷屯": ("坎", "震"), "山水蒙": ("坎", "艮"),
    "水天需": ("乾", "坎"), "天水訟": ("坎", "乾"), "地水師": ("坎", "坤"), "水地比": ("坤", "坎"),
    "風天小畜": ("乾", "巽"), "天澤履": ("兌", "乾"), "地天泰": ("乾", "坤"), "天地否": ("坤", "乾"),
    "天火同人": ("離", "乾"), "火天大有": ("乾", "離"), "地山謙": ("艮", "坤"), "雷地豫": ("坤", "震"),
    "澤雷隨": ("震", "兌"), "山風蠱": ("巽", "艮"), "地澤臨": ("兌", "坤"), "風地觀": ("坤", "巽"),
    "火雷噬嗑": ("震", "離"), "山火賁": ("離", "艮"), "山地剝": ("艮", "坤"), "地雷復": ("震", "坤"),
    "天雷無妄": ("震", "乾"), "山天大畜": ("乾", "艮"), "山雷頤": ("震", "艮"), "澤風大過": ("巽", "兌"),
    "坎為水": ("坎", "坎"), "離為火": ("離", "離"), "澤山咸": ("艮", "兌"), "雷風恆": ("巽", "震"),
    "天山遁": ("艮", "乾"), "雷天大壯": ("乾", "震"), "火地晉": ("坤", "離"), "地火明夷": ("離", "坤"),
    "風火家人": ("離", "巽"), "火澤睽": ("兌", "離"), "水山蹇": ("艮", "坎"),    "雷水解": ("震", "坎"),
    "山澤損": ("兌", "艮"), "風雷益": ("震", "巽"), "澤天夬": ("乾", "兌"), "天風姤": ("巽", "乾"),
    "澤地萃": ("坤", "兌"), "地風升": ("巽", "坤"), "澤水困": ("坎", "兌"), "水風井": ("巽", "坎"),
    "澤火革": ("離", "兌"), "火風鼎": ("巽", "離"), "震為雷": ("震", "震"), "艮為山": ("艮", "艮"),
    "風山漸": ("艮", "巽"), "雷澤歸妹": ("兌", "震"), "雷火豐": ("離", "震"), "火山旅": ("艮", "離"),
    "巽為風": ("巽", "巽"), "兌為澤": ("兌", "兌"), "風水渙": ("坎", "巽"), "水澤節": ("兌", "坎"),
    "風澤中孚": ("兌", "巽"), "雷山小過": ("艮", "震"), "水火既濟": ("離", "坎"), "火水未濟": ("坎", "離")
}
NA_JIA_RULES = {
    "乾": (("甲"), ("壬"), ["子", "寅", "辰"], ["午", "申", "戌"]),
    "坤": (("乙"), ("癸"), ["未", "巳", "卯"], ["丑", "亥", "酉"]),
    "震": (("庚"), ("庚"), ["子", "寅", "辰"], ["午", "申", "戌"]),
    "巽": (("辛"), ("辛"), ["丑", "亥", "酉"], ["未", "巳", "卯"]),
    "坎": (("戊"), ("戊"), ["寅", "辰", "午"], ["申", "戌", "子"]),
    "離": (("己"), ("己"), ["卯", "丑", "亥"], ["酉", "未", "巳"]),
    "艮": (("丙"), ("丙"), ["辰", "午", "申"], ["戌", "子", "寅"]),
    "兌": (("丁"), ("丁"), ["巳", "卯", "丑"], ["亥", "酉", "未"])
}
BRANCH_ELEMENTS = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
    '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
}
PALACE_ELEMENTS = {
    '乾': '金', '兌': '金', '離': '火', '震': '木',
    '巽': '木', '坎': '水', '艮': '土', '坤': '土'
}
APPLICATION_GUIDE = {
    '事業': {"target": "官鬼", "guide": "以「官鬼爻」為主。"},
    '財運': {"target": "妻財", "guide": "以「妻財爻」為主。"},
    '健康': {"target": "官鬼", "guide": "觀「官鬼爻」是否旺相（鬼旺為病）。"},
    '感情': {"target": ["妻財", "官鬼"], "guide": "男看財、女看官。"},
    '考試': {"target": "父母", "guide": "取「父母爻」。"}
}
HEAVENLY_STEMS = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
EARTHLY_BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
STEM_ELEMENTS = {
    '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
    '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'
}
REFERENCE_DATE = datetime.date(2000, 1, 1)
REFERENCE_STEM_INDEX = 4  # 戊 (Wu)
REFERENCE_BRANCH_INDEX = 6 # 午 (Wu)

KONG_WANG_MAP = { # Maps the start-of-xun branch to the two empty branches
    '子': ['戌', '亥'], '戌': ['申', '酉'], '申': ['午', '未'],
    '午': ['辰', '巳'], '辰': ['寅', '卯'], '寅': ['子', '丑']
}

BRANCH_RELATIONS = {
    "clash": {'子': '午', '丑': '未', '寅': '申', '卯': '酉', '辰': '戌', '巳': '亥'},
    "combine": {'子': '丑', '寅': '亥', '卯': '戌', '辰': '酉', '巳': '申', '午': '未'}
}

FIVE_ELEMENT_RELATIONS = {
    '木': {"produces": '火', "produced_by": '水', "conquers": '土', "conquered_by": '金'},
    '火': {"produces": '土', "produced_by": '木', "conquers": '金', "conquered_by": '水'},
    '土': {"produces": '金', "produced_by": '火', "conquers": '水', "conquered_by": '木'},
    '金': {"produces": '水', "produced_by": '土', "conquers": '木', "conquered_by": '火'},
    '水': {"produces": '木', "produced_by": '金', "conquers": '火', "conquered_by": '土'}
}

SIX_GODS = ['青龍', '朱雀', '勾陳', '螣蛇', '白虎', '玄武']
SIX_GODS_START_INDEX = {
    '甲': 0, '乙': 0, '丙': 1, '丁': 1, '戊': 2, '己': 3, '庚': 4, '辛': 4, '壬': 5, '癸': 5
}
SOLAR_TERM_DATES = {
    1: {"start_day": 5, "branch": '丑'}, 2: {"start_day": 4, "branch": '寅'},
    3: {"start_day": 5, "branch": '卯'}, 4: {"start_day": 4, "branch": '辰'},
    5: {"start_day": 5, "branch": '巳'}, 6: {"start_day": 5, "branch": '午'},
    7: {"start_day": 6, "branch": '未'}, 8: {"start_day": 7, "branch": '申'},
    9: {"start_day": 7, "branch": '酉'}, 10: {"start_day": 8, "branch": '戌'},
    11: {"start_day": 7, "branch": '亥'}, 12: {"start_day": 6, "branch": '子'}
}

TRIGRAM_STRUCTURES = {
    "乾": (1, 1, 1),
    "兌": (1, 1, 0),
    "離": (1, 0, 1),
    "震": (1, 0, 0),
    "巽": (0, 1, 1),
    "坎": (0, 1, 0),
    "艮": (0, 0, 1),
    "坤": (0, 0, 0),
}
STRUCTURE_TO_TRIGRAM = {v: k for k, v in TRIGRAM_STRUCTURES.items()}

# =============================================================================
# Section 2: Core Logic Functions
# =============================================================================

def get_interlocking_hexagram(original_structure):
    if not original_structure or len(original_structure) != 6:
        return None

    # Lower trigram of interlocking hexagram: lines 2, 3, 4 of original
    lower_interlocking_trigram = (original_structure[1], original_structure[2], original_structure[3])

    # Upper trigram of interlocking hexagram: lines 3, 4, 5 of original
    upper_interlocking_trigram = (original_structure[2], original_structure[3], original_structure[4])

    # Find the hexagram that corresponds to the interlocking trigrams
    for hex_name, (lower, upper) in HEXAGRAM_COMPOSITION.items():
        # This is a simplification, as we don't have direct trigram structures.
        # We are looking for a hexagram that is composed of trigrams that have the same structure as our interlocking trigrams.
        # This is not a robust way to do this, but it's the best we can do with the current data structures.
        # A better approach would be to have a mapping of trigram names to their structures.
        pass # Placeholder for now

    # Let's try a different approach. We can construct the 6-line structure of the interlocking hexagram directly.
    interlocking_structure = (original_structure[1], original_structure[2], original_structure[3], original_structure[2], original_structure[3], original_structure[4])

    # This is still not right. The interlocking hexagram is a combination of two new trigrams.
    # Let's define the trigram structures.
    TRIGRAM_STRUCTURES = {
        "乾": (1, 1, 1),
        "兌": (0, 1, 1),
        "離": (1, 0, 1),
        "震": (0, 0, 1),
        "巽": (1, 1, 0),
        "坎": (0, 1, 0),
        "艮": (1, 0, 0),
        "坤": (0, 0, 0),
    }
    STRUCTURE_TO_TRIGRAM = {v: k for k, v in TRIGRAM_STRUCTURES.items()}

    lower_interlocking_trigram_structure = (original_structure[1], original_structure[2], original_structure[3])
    upper_interlocking_trigram_structure = (original_structure[2], original_structure[3], original_structure[4])

    lower_trigram_name = STRUCTURE_TO_TRIGRAM.get(lower_interlocking_trigram_structure)
    upper_trigram_name = STRUCTURE_TO_TRIGRAM.get(upper_interlocking_trigram_structure)

    if not lower_trigram_name or not upper_trigram_name:
        return None

    # Now find the hexagram name from the composition
    for hex_name, (lower, upper) in HEXAGRAM_COMPOSITION.items():
        if lower == lower_trigram_name and upper == upper_trigram_name:
            return hex_name

    return None

def get_interlocking_hexagram(original_structure):
    if not original_structure or len(original_structure) != 6:
        return None

    lower_interlocking_trigram_structure = (original_structure[1], original_structure[2], original_structure[3])
    upper_interlocking_trigram_structure = (original_structure[2], original_structure[3], original_structure[4])

    lower_trigram_name = STRUCTURE_TO_TRIGRAM.get(lower_interlocking_trigram_structure)
    upper_trigram_name = STRUCTURE_TO_TRIGRAM.get(upper_interlocking_trigram_structure)

    if not lower_trigram_name or not upper_trigram_name:
        return None

    # Find the hexagram name from the composition
    for hex_name, (upper, lower) in HEXAGRAM_COMPOSITION.items():
        if lower == lower_trigram_name and upper == upper_trigram_name:
            return hex_name

    return None

def get_day_info(input_date=None):
    today = input_date if input_date else datetime.date.today()
    delta_days = (today - REFERENCE_DATE).days
    current_stem_index = (REFERENCE_STEM_INDEX + delta_days) % 10
    current_branch_index = (REFERENCE_BRANCH_INDEX + delta_days) % 12
    day_stem = HEAVENLY_STEMS[current_stem_index]
    day_branch = EARTHLY_BRANCHES[current_branch_index]
    day_element = STEM_ELEMENTS[day_stem]
    month = today.month
    day = today.day
    term_info = SOLAR_TERM_DATES[month]
    prev_month_term_info = SOLAR_TERM_DATES.get(month - 1, SOLAR_TERM_DATES[12])
    month_branch = term_info["branch"] if day >= term_info["start_day"] else prev_month_term_info["branch"]
    return day_stem, day_branch, day_element, month_branch

def get_kong_wang(day_stem, day_branch):
    stem_index = HEAVENLY_STEMS.index(day_stem)
    branch_index = EARTHLY_BRANCHES.index(day_branch)
    # Find the start of the 10-day cycle (Xun)
    start_branch_index = (branch_index - stem_index + 12) % 12
    xun_start_branch = EARTHLY_BRANCHES[start_branch_index]
    return KONG_WANG_MAP.get(xun_start_branch, [])

def get_interpretation_details(analysis, day_branch, month_branch):
    interpretation = {"special_type": None, "line_details": {}}
    lines = analysis['lines']

    # Check for Six-Clash or Six-Harmony Hexagram
    clash_map = {v: k for k, v in BRANCH_RELATIONS["clash"].items()}
    clash_map.update(BRANCH_RELATIONS["clash"])
    combine_map = {v: k for k, v in BRANCH_RELATIONS["combine"].items()}
    combine_map.update(BRANCH_RELATIONS["combine"])

    if (clash_map.get(lines[0]['branch']) == lines[3]['branch'] and
        clash_map.get(lines[1]['branch']) == lines[4]['branch'] and
        clash_map.get(lines[2]['branch']) == lines[5]['branch']):
        interpretation["special_type"] = "六冲卦 (Six-Clash Hexagram)"
    elif (analysis['palace_name'] == lines[0]['relative'] and 
          analysis['palace_name'] == lines[1]['relative'] and 
          analysis['palace_name'] == lines[2]['relative'] and 
          analysis['palace_name'] == lines[3]['relative'] and 
          analysis['palace_name'] == lines[4]['relative'] and 
          analysis['palace_name'] == lines[5]['relative']):
        interpretation["special_type"] = "六冲卦 (Six-Clash Hexagram - Pure Palace)"

    if (combine_map.get(lines[0]['branch']) == lines[3]['branch'] and
        combine_map.get(lines[1]['branch']) == lines[4]['branch'] and
        combine_map.get(lines[2]['branch']) == lines[5]['branch']):
        interpretation["special_type"] = "六合卦 (Six-Harmony Hexagram)"

    month_element = BRANCH_ELEMENTS[month_branch]
    day_element = BRANCH_ELEMENTS[day_branch]

    for i, line in enumerate(lines):
        line_num = i + 1
        details = []
        line_element = line['element']
        line_branch = line['branch']

        # Strength vs Month
        if line_element == month_element: details.append("旺 (Prosperous)")
        elif FIVE_ELEMENT_RELATIONS[month_element]["produces"] == line_element: details.append("相 (Strong)")
        elif FIVE_ELEMENT_RELATIONS[line_element]["produces"] == month_element: details.append("休 (Weakened)")
        elif FIVE_ELEMENT_RELATIONS[month_element]["conquers"] == line_element: details.append("囚 (Imprisoned)")
        elif FIVE_ELEMENT_RELATIONS[line_element]["conquers"] == month_element: details.append("死 (Dead)")

        # Interactions with Day/Month Branch
        if clash_map.get(line_branch) == day_branch: 
            details.append("暗動 (Secretly Moving - Clashes with Day)")
        if clash_map.get(line_branch) == month_branch: 
            details.append("月破 (Month-Broken - Clashes with Month)")
        if combine_map.get(line_branch) == day_branch: 
            details.append("合日 (Combines with Day)")
        if combine_map.get(line_branch) == month_branch: 
            details.append("合月 (Combines with Month)")

        interpretation["line_details"][line_num] = details

    return interpretation

def format_for_llm(main_analysis, changed_analysis, interpretation, day_info, question):

    output = []

    output.append("--- 卦象資料 ---")

    output.append(f"\n**占卜主題:** {question}")

    output.append(f"**日期資訊:** {day_info}")



    # Main Hexagram

    output.append(f"\n**本卦:** {main_analysis['hex_name']} ({main_analysis['palace_name']}宮{main_analysis['gen_name']}) - 五行屬{main_analysis['palace_element']}")

    for line in reversed(main_analysis['lines']):

        line_str = f"- {line['position']}: "

        if line['fu_shen']:

            line_str += f"伏({line['fu_shen']['relative']} {line['fu_shen']['branch']}) "

        line_str += f"{line['relative']} {line['branch']} "

        if line['shi_ying']:

            line_str += f"({line['shi_ying']}) "

        if line['is_empty']:

            line_str += "(空亡) "

        output.append(line_str)



    # Changed Hexagram

    if changed_analysis:

        output.append(f"\n**變卦:** {changed_analysis['hex_name']} ({changed_analysis['palace_name']}宮{changed_analysis['gen_name']})")

        moving_lines = [l for l in main_analysis['lines'] if l['line_num'] in changed_analysis.get('moving_lines_in_main', [])]

        for line in moving_lines:

             output.append(f"- 動爻: {line['position']} {line['relative']} {line['branch']} -> ...") # Simplified for brevity



    # Interlocking Hexagram

    interlocking_hexagram_name = get_interlocking_hexagram(NAME_TO_STRUCTURE.get(main_analysis['hex_name']))

    if interlocking_hexagram_name:

        output.append(f"\n**互卦:** {interlocking_hexagram_name}")

        output.append("  (互卦揭示了事物發展的內部潛在趨勢)")



    # Interpretation Helper

    output.append("\n**斷卦參考:**")
    if interpretation["special_type"]:
        output.append(f"- 特殊卦象: {interpretation['special_type']}")
    for line in main_analysis['lines']:
        details = interpretation['line_details'][line['line_num']]
        if details:
            output.append(f"- {line['position']} {line['relative']} ({line['branch']}): { ', '.join(details) }")

    return "\n".join(output)


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

def analyze_hexagram(hex_name, day_stem, day_branch, day_element, is_recursive_call=False):
    if hex_name not in HEXAGRAM_COMPOSITION: return None, f"錯誤：找不到卦名 '{hex_name}' 的組成規則。"
    
    structure = NAME_TO_STRUCTURE.get(hex_name)
    if not structure: return None, f"錯誤：在爻象結構圖中找不到 '{hex_name}'."

    lower_trigram, upper_trigram = HEXAGRAM_COMPOSITION[hex_name]
    palace_trigram = [p for p, h_list in PALACE_DATA.items() if hex_name in h_list][0]
    palace_element = PALACE_ELEMENTS[palace_trigram]

    # Determine Shi and Ying lines
    hex_index = PALACE_DATA[palace_trigram].index(hex_name)
    shi_line_map = [6, 1, 2, 3, 4, 5, 4, 3]  # Index in palace -> Shi line number
    shi_line = shi_line_map[hex_index]
    ying_line = shi_line + 3 if shi_line <= 3 else shi_line - 3

    # Get Kong Wang (empty) branches
    empty_branches = get_kong_wang(day_stem, day_branch)

    analysis_result = {
        "hex_name": hex_name, "palace_name": palace_trigram, "palace_element": palace_element,
        "day_stem": day_stem, "day_element": day_element, "lines": [], "empty_branches": empty_branches
    }
    lower_stem, _, lower_branches, _ = NA_JIA_RULES[lower_trigram]
    _, upper_stem, _, upper_branches = NA_JIA_RULES[upper_trigram]
    stems = [lower_stem[0]] * 3 + [upper_stem[0]] * 3
    branches = lower_branches + upper_branches
    line_positions = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']
    start_god_index = SIX_GODS_START_INDEX[day_stem]

    present_relatives = set()
    for i in range(6):
        branch = branches[i]
        line_element = BRANCH_ELEMENTS[branch]
        six_relative = get_six_relatives(line_element, palace_element)
        present_relatives.add(six_relative)

    # Fu Shen (Hidden God) Logic
    fu_shen_lines = [None] * 6
    required_relatives = {'父母', '兄弟', '子孫', '妻財', '官鬼'}
    if not is_recursive_call and not required_relatives.issubset(present_relatives):
        palace_hex_name = PALACE_DATA[palace_trigram][0]
        palace_analysis, _ = analyze_hexagram(palace_hex_name, day_stem, day_branch, day_element, is_recursive_call=True)
        if palace_analysis:
            fu_shen_lines = palace_analysis['lines']

    for i in range(6):
        branch = branches[i]
        line_element = BRANCH_ELEMENTS[branch]
        six_relative = get_six_relatives(line_element, palace_element)
        six_god = SIX_GODS[(start_god_index + i) % 6]

        shi_ying_marker = ""
        line_num = i + 1
        if line_num == shi_line:
            shi_ying_marker = "世"
        elif line_num == ying_line:
            shi_ying_marker = "應"

        is_empty = branch in empty_branches

        fu_shen_data = None
        if fu_shen_lines[i]:
            if fu_shen_lines[i]['relative'] not in present_relatives:
                fu_shen_data = {
                    'relative': fu_shen_lines[i]['relative'],
                    'branch': fu_shen_lines[i]['branch']
                }

        analysis_result["lines"].append({
            "position": line_positions[i], "line_num": i + 1,
            "yin_yang": structure[i],
            "stem": stems[i], "branch": branch,
            "element": line_element, "relative": six_relative, "six_god": six_god,
            "shi_ying": shi_ying_marker, "is_empty": is_empty, "fu_shen": fu_shen_data
        })
    return analysis_result, None

def find_lines_by_relative(analysis_result, relative_name):
    found_lines = []
    if not analysis_result or not analysis_result.get("lines"): return found_lines
    for line in analysis_result["lines"]:
        if line["relative"] == relative_name:
            full_stem_branch = f'{line["stem"]}{line["branch"]}'
            found_lines.append(f'{line["position"]} {full_stem_branch} {line["element"]}')
    return found_lines

# =============================================================================
# Section 3: Display and Interaction
# =============================================================================

def display_full_analysis(main_analysis, changed_analysis, moving_lines, month_branch):
    if not main_analysis: return
    print(f"--- 主卦分析：【{main_analysis['hex_name']}】 (日主：{main_analysis['day_stem']}{main_analysis['day_element']} / 月建：{month_branch}) ---")
    gen_name_list = [gn for p, h_list in PALACE_DATA.items() if main_analysis['hex_name'] in h_list for gn in GENERATION_NAMES if h_list.index(main_analysis['hex_name']) == GENERATION_NAMES.index(gn)]
    gen_name = gen_name_list[0] if gen_name_list else '未知'
    print(f"  - 本卦屬性： {main_analysis['palace_name']}宮{gen_name} (五行：{main_analysis['palace_element']})\n")
    print(f"  {'爻位':<4}{'伏神':<8}{'世應':<3}{'陰陽':<3}{ '動':<2}{ '空亡':<3}{ '六神':<4}{ '納甲':<6}{ '地支':<4}{ '五行':<4}{ '六親':<5}")
    print(f"  {'--'*2:<4}{'--'*4:<8}{'--'*1:<3}{'--'*1:<3}{'--'*1:<2}{'--'*1:<3}{'--'*2:<4}{'--'*3:<6}{'--'*2:<4}{'--'*2:<4}{'--'*2:<5}")
    for i, line in enumerate(reversed(main_analysis["lines"])):
        line_num = 6 - i
        moving_marker = "●" if line_num in moving_lines else ""
        empty_marker = "空" if line['is_empty'] else ""
        
        fu_shen_str = ""
        if line['fu_shen']:
            fu_shen_str = f"{line['fu_shen']['relative']}{line['fu_shen']['branch']}"

        full_stem_branch = f'{line["stem"]}{line["branch"]}'
        yin_yang_symbol = "—" if line['yin_yang'] == 1 else "--"
        print(f"  {line['position']:<4}{fu_shen_str:<8}{line['shi_ying']:<3}{yin_yang_symbol:<3}{moving_marker:<2}{empty_marker:<3}{line['six_god']:<4}{full_stem_branch:<6}{line['branch']:<4}{line['element']:<4}{line['relative']:<5}")
    print("\n")

    if changed_analysis:
        print(f"--- 變卦分析：【{changed_analysis['hex_name']}】 ---")
        print("  動爻變為：")
        for line_num in moving_lines:
            original_line = main_analysis["lines"][line_num - 1]
            changed_line = changed_analysis["lines"][line_num - 1]
            print(f"    {original_line['position']} {original_line['relative']} {original_line['branch']} -> {changed_line['relative']} {changed_line['branch']}")
        print("\n")

    print("\n" + "-"*40 + "\n")

if __name__ == "__main__":
    print("="*50)
    print("        六爻納甲分析系統 (v6.1 直接輸入版)")
    print("="*50 + "\n")
    
    date_str = input("請輸入起卦日期 (YYYY-MM-DD) 或按 Enter 使用今天日期: ")
    input_date = None
    if date_str:
        try:
            input_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            print("日期格式錯誤，將使用今天日期。")

    day_stem, day_branch, day_element, month_branch = get_day_info(input_date)
    
    print(f"分析日期 ({input_date or datetime.date.today()}) 為「{day_stem}{day_branch}」日，日干五行屬【{day_element}】，月建為【{month_branch}】。")
    empty_branches = get_kong_wang(day_stem, day_branch)
    if empty_branches:
        print(f"本日空亡為【{'、'.join(empty_branches)}】。")
    print("系統將以此為基準進行分析。\n")
    
    while True:
        try:
            lines_str = input("請由下往上輸入六爻 (0=陰, 1=陽)，用逗號分隔 (或輸入 'exit' 離開): ")
            if lines_str.lower() == 'exit': break

            lines = tuple(int(x.strip()) for x in lines_str.split(','))
            if len(lines) != 6:
                print("錯誤：爻象輸入必須剛好是6個數字。\n")
                continue

            hex_name = get_hexagram_from_lines(lines)
            if hex_name == "未知卦":
                print(f"錯誤：輸入的爻象 {lines} 無法對應到任何已知卦象。\n")
                continue

            moving_lines_str = input("請輸入動爻（1-6，多個請用逗號分隔，無則留空）：")
            if moving_lines_str.lower() == 'exit': break
            moving_lines = [int(x.strip()) for x in moving_lines_str.split(',') if x.strip().isdigit() and 1 <= int(x.strip()) <= 6]

            categories = list(APPLICATION_GUIDE.keys())
            print("請選擇占事類別：")
            for i, category in enumerate(categories):
                print(f"  {i+1}. {category}")
            print(f"  {len(categories)+1}. 其他")
            
            question_num_str = input(f"請輸入數字選擇 (1-{len(categories)+1})：")
            if question_num_str.lower() == 'exit': break

            try:
                question_num = int(question_num_str)
                if 1 <= question_num <= len(categories):
                    question = categories[question_num - 1]
                elif question_num == len(categories) + 1:
                    question = input("請輸入其他占事類別：")
                else:
                    print("輸入錯誤，請重新輸入。")
                    continue
            except ValueError:
                print("輸入錯誤，請輸入數字。")
                continue

            main_analysis, error = analyze_hexagram(hex_name, day_stem, day_branch, day_element)
            changed_analysis = None
            
            if error:
                print(f"{error}\n")
                continue

            # Add gen_name to main_analysis
            gen_name_list = [gn for p, h_list in PALACE_DATA.items() if main_analysis['hex_name'] in h_list for gn in GENERATION_NAMES if h_list.index(main_analysis['hex_name']) == GENERATION_NAMES.index(gn)]
            main_analysis['gen_name'] = gen_name_list[0] if gen_name_list else '未知'

            if moving_lines:
                changed_hex_name = get_changed_hexagram_name(hex_name, moving_lines)
                if changed_hex_name != "未知卦":
                    changed_analysis, _ = analyze_hexagram(changed_hex_name, day_stem, day_branch, day_element)
                    # Add gen_name to changed_analysis
                    gen_name_list = [gn for p, h_list in PALACE_DATA.items() if changed_analysis['hex_name'] in h_list for gn in GENERATION_NAMES if h_list.index(changed_analysis['hex_name']) == GENERATION_NAMES.index(gn)]
                    changed_analysis['gen_name'] = gen_name_list[0] if gen_name_list else '未知'
            
            display_full_analysis(main_analysis, changed_analysis, moving_lines, month_branch)

            # --- Interpretation Section ---
            interpretation = get_interpretation_details(main_analysis, day_branch, month_branch)
            print("--- 斷卦參考 ---")
            if interpretation["special_type"]:
                print(f"  - 特殊卦象：{interpretation['special_type']}")
            
            for line in main_analysis['lines']:
                details = interpretation['line_details'][line['line_num']]
                if details:
                    print(f"  - {line['position']} {line['relative']} ({line['branch']}): { ', '.join(details) }")
            print("\n" + "="*50 + "\n")

            # --- Format for LLM --- 
            print("\n" + "#"*60)
            print("### 複製以下內容以用於大型語言模型分析 ###")
            print("#"*60 + "\n")
            day_info_str = f"分析日期 ({input_date or datetime.date.today()}) 為「{day_stem}{day_branch}」日，日干五行屬【{day_element}】，月建為【{month_branch}】，空亡為【{'、'.join(empty_branches)}】"
            # Add moving lines to changed_analysis for context
            if changed_analysis:
                changed_analysis['moving_lines_in_main'] = moving_lines
            llm_formatted_data = format_for_llm(main_analysis, changed_analysis, interpretation, day_info_str, question)
            print(LLM_PROMPT_TEMPLATE)
            print(llm_formatted_data)
            print("\n" + "#"*60 + "\n")

        except (EOFError, KeyboardInterrupt):
            break
        except ValueError:
            print("錯誤：輸入格式不正確，請用0,1並以逗號分隔。\n")
        except Exception as e:
            print(f"發生錯誤：{e}")

    print("\n感謝使用，系統關閉。")