# -*- coding: utf-8 -*-
from typing import List, Tuple, Dict

# =============================================================================
# Section 1: Data Definitions
# Using the user-provided and confirmed HEXAGRAM_MAP as the single source of truth.
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
    (1, 1, 0, 1, 1, 0): "澤火革",
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

# =============================================================================
# Section 2: Core Interpretation Function
# =============================================================================

def get_hexagram_from_lines(lines: Tuple[int, ...]) -> str:
    return HEXAGRAM_MAP.get(lines, "未知卦")

def interpret_hexagrams_from_lines(lines: List[int], moving_lines: List[int] = None) -> Dict:
    if len(lines) != 6:
        return {"error": "輸入必須剛好是6個爻 (0或1)。"}

    result = {}
    main_lines_tuple = tuple(lines)
    main_hex_name = get_hexagram_from_lines(main_lines_tuple)
    result["主卦"] = {"name": main_hex_name, "lines": main_lines_tuple}

    # Interlocked Hexagram
    interlocked_lower_lines = tuple(lines[1:4])
    interlocked_upper_lines = tuple(lines[2:5])
    interlocked_structure = interlocked_lower_lines + interlocked_upper_lines
    interlocked_hex_name = get_hexagram_from_lines(interlocked_structure)
    result["互卦"] = {"name": interlocked_hex_name, "lines": interlocked_structure}

    # Changed Hexagram
    if moving_lines:
        changed_lines = list(lines)
        for line_num in moving_lines:
            if 1 <= line_num <= 6:
                changed_lines[line_num - 1] = 1 - changed_lines[line_num - 1]
        
        changed_lines_tuple = tuple(changed_lines)
        changed_hex_name = get_hexagram_from_lines(changed_lines_tuple)
        result["變卦"] = {"name": changed_hex_name, "lines": changed_lines_tuple}
    
    return result

# =============================================================================
# Section 3: Demonstration
# =============================================================================

if __name__ == "__main__":
    print("--- 案例一：驗證『歸妹』變卦 ---")
    # Per user's map, 歸妹 is (1, 1, 0, 1, 0, 0)
    case1_lines = [1, 1, 0, 1, 0, 0]
    case1_moving = [3]
    print(f"輸入爻象: {case1_lines} (雷澤歸妹)")
    print(f"動爻位置: {case1_moving}\n")
    analysis1 = interpret_hexagrams_from_lines(case1_lines, case1_moving)
    if "error" in analysis1:
        print(analysis1["error"])
    else:
        print(f"主卦: 【{analysis1['主卦']['name']}】")
        print(f"互卦: 【{analysis1['互卦']['name']}】")
        if "變卦" in analysis1:
            print(f"變卦: 【{analysis1['變卦']['name']}】")
    
    print("\n" + "="*30 + "\n")

    print("--- 案例二：驗證您測試的爻象 ---")
    case2_lines = [1, 1, 0, 1, 0, 0]
    print(f"輸入爻象: {case2_lines}\n")
    analysis2 = interpret_hexagrams_from_lines(case2_lines)
    if "error" in analysis2:
        print(analysis2["error"])
    else:
        print(f"主卦: 【{analysis2['主卦']['name']}】")
        print(f"互卦: 【{analysis2['互卦']['name']}】")
