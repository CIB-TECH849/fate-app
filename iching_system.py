
# -*- coding: utf-8 -*-

# --- 資料定義區 ---

# 1. 八宮卦系總覽
PALACE_DATA = {
    "乾": ["乾", "姤", "遯", "否", "觀", "剝", "晉", "大有"],
    "震": ["震", "豫", "解", "恒", "升", "井", "大過", "隨"],
    "坎": ["坎", "節", "屯", "既濟", "革", "豐", "明夷", "師"],
    "艮": ["艮", "賁", "大畜", "損", "睽", "履", "中孚", "漸"],
    "坤": ["坤", "復", "臨", "泰", "大壯", "夬", "需", "比"],
    "巽": ["巽", "小畜", "家人", "益", "无妄", "噬嗑", "頤", "蠱"],
    "離": ["離", "旅", "鼎", "未濟", "蒙", "渙", "訟", "同人"],
    "兌": ["兌", "困", "萃", "咸", "蹇", "謙", "小過", "歸妹"]
}

# 2. 卦宮世系名稱
GENERATION_NAMES = ["本宮卦", "一世卦", "二世卦", "三世卦", "四世卦", "五世卦", "游魂卦", "歸魂卦"]

# 3. 卦宮世系意涵
GENERATION_MEANINGS = {
    "本宮卦": "此宮的根本卦，代表起始狀態或本質。",
    "一世卦": "象徵事物的初動與萌芽。",
    "二世卦": "事物的發展期。",
    "三世卦": "事物的成熟或定形。",
    "四世卦": "轉變或突破階段。",
    "五世卦": "進入盛極或末期。",
    "游魂卦": "象徵漂泊、不安或失根之象。",
    "歸魂卦": "回歸本源、結束與歸藏之象。"
}

# --- 核心計算函式 ---

def find_hexagram_details(hex_name):
    """
    查詢指定卦名的詳細資訊。
    :param hex_name: 要查詢的卦名 (例如 "剝")
    :return: 一個包含詳細資訊的字典，如果找不到則回傳 None
    """
    for palace, hexagrams in PALACE_DATA.items():
        if hex_name in hexagrams:
            index = hexagrams.index(hex_name)
            gen_name = GENERATION_NAMES[index]
            
            return {
                "input": hex_name,
                "palace": palace,
                "generation_name": gen_name,
                "generation_meaning": GENERATION_MEANINGS[gen_name],
                "root_hexagram": hexagrams[0]
            }
    return None

# --- 系統執行與互動 ---

def display_details(hex_name):
    """
    根據卦名顯示其詳細資訊。
    """
    result = find_hexagram_details(hex_name)
    
    print(f"--- 查詢結果：【{hex_name}】---")
    if result:
        meaning = result['generation_meaning']
        summary = ""
        if '，' in meaning:
            summary = meaning.split('，')[1].rstrip('。')
        else:
            summary = meaning.rstrip('。')

        print(f"  - 所屬卦宮： {result['palace']}宮")
        print(f"  - 卦宮世序： {result['generation_name']}")
        print(f"  - 世序意涵： {result['generation_meaning']}")
        print(f"  - 應用說明： 若得【{result['input']}卦】，可知為 {result['palace']}宮{result['generation_name']}，")
        print(f"               象徵「{summary}」。")
    else:
        print(f"  在八宮卦系中找不到【{hex_name}】這個卦。")
    print("\n" + "="*30 + "\n")

if __name__ == "__main__":
    # 歡迎訊息
    print("="*30)
    print("    八宮卦系查詢系統")
    print("="*30 + "\n")

    # 根據您提供的範例進行查詢
    print("以下是根據您文件中的範例進行的查詢：\n")
    
    # 範例一：查詢「剝」
    display_details("剝")
    
    # 範例二：查詢「恒」
    display_details("恒")

    # 範例三：查詢一個不存在的卦
    display_details("測試")
