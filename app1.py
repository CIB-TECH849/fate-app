from flask import Flask, render_template_string, request, redirect, url_for, flash
import re
import os
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'a_secret_key_for_flashing_messages'  # 用於快閃訊息

SQL_FILE_PATH = os.path.join(os.path.dirname(__file__), 'yilin.sql')

# --- 節氣資料 ---

jieqi_names = [
    "小寒", "大寒", "立春", "雨水", "驚蟄", "春分",
    "清明", "穀雨", "立夏", "小滿", "芒種", "夏至",
    "小暑", "大暑", "立秋", "處暑", "白露", "秋分",
    "寒露", "霜降", "立冬", "小雪", "大雪", "冬至"
]

jieqi_table = {
    2025: ([
        "2025-01-05","2025-01-20","2025-02-03","2025-02-18",
        "2025-03-05","2025-03-20","2025-04-04","2025-04-20",
        "2025-05-05","2025-05-21","2025-06-05","2025-06-21",
        "2025-07-07","2025-07-22","2025-08-07","2025-08-23",
        "2025-09-07","2025-09-23","2025-10-08","2025-10-23",
        "2025-11-07","2025-11-22","2025-12-07","2025-12-21"
    ], []),
    2026: ([
        "2026-01-05","2026-01-20","2026-02-04","2026-02-18",
        "2026-03-05","2026-03-20","2026-04-05","2026-04-20",
        "2026-05-05","2026-05-21","2026-06-05","2026-06-21",
        "2026-07-07","2026-07-23","2026-08-07","2026-08-23",
        "2026-09-07","2026-09-23","2026-10-08","2026-10-23",
        "2026-11-07","2026-11-22","2026-12-07","2026-12-22"
    ], []),
    2027: ([
        "2027-01-05","2027-01-20","2027-02-04","2027-02-19",
        "2027-03-06","2027-03-21","2027-04-05","2027-04-20",
        "2027-05-06","2027-05-21","2027-06-06","2027-06-21",
        "2027-07-07","2027-07-23","2027-08-08","2027-08-23",
        "2027-09-08","2027-09-23","2027-10-08","2027-10-23",
        "2027-11-07","2027-11-22","2027-12-07","2027-12-22"
    ], []),
    2028: ([
        "2028-01-06","2028-01-20","2028-02-04","2028-02-19",
        "2028-03-05","2028-03-20","2028-04-04","2028-04-19",
        "2028-05-05","2028-05-20","2028-06-05","2028-06-21",
        "2028-07-06","2028-07-22","2028-08-07","2028-08-22",
        "2028-09-07","2028-09-22","2028-10-08","2028-10-23",
        "2028-11-07","2028-11-22","2028-12-06","2028-12-21"
    ], []),
    2029: ([
        "2029-01-05","2029-01-20","2029-02-03","2029-02-18",
        "2029-03-05","2029-03-20","2029-04-04","2029-04-20",
        "2029-05-05","2029-05-21","2029-06-05","2029-06-21",
        "2029-07-07","2029-07-22","2029-08-07","2029-08-23",
        "2029-09-07","2029-09-23","2029-10-08","2029-10-23",
        "2029-11-07","2029-11-22","2029-12-07","2029-12-21"
    ], []),
    2030: ([
        "2030-01-05","2030-01-20","2030-02-04","2030-02-18",
        "2030-03-05","2030-03-20","2030-04-05","2030-04-20",
        "2030-05-05","2030-05-21","2030-06-05","2030-06-21",
        "2030-07-07","2030-07-23","2030-08-07","2030-08-23",
        "2030-09-07","2030-09-23","2030-10-08","2030-10-23",
        "2030-11-07","2030-11-22","2030-12-07","2030-12-22"
    ], []),
    2031: ([
        "2031-01-05","2031-01-20","2031-02-04","2031-02-19",
        "2031-03-06","2031-03-21","2031-04-05","2031-04-20",
        "2031-05-06","2031-05-21","2031-06-06","2031-06-21",
        "2031-07-07","2031-07-23","2031-08-08","2031-08-23",
        "2031-09-08","2031-09-23","2031-10-08","2031-10-23",
        "2031-11-07","2031-11-22","2031-12-07","2031-12-22"
    ], []),
    2032: ([
        "2032-01-06","2032-01-20","2032-02-04","2032-02-19",
        "2032-03-05","2032-03-20","2032-04-04","2032-04-19",
        "2032-05-05","2032-05-20","2032-06-05","2032-06-21",
        "2032-07-06","2032-07-22","2032-08-07","2032-08-22",
        "2032-09-07","2032-09-22","2032-10-08","2032-10-23",
        "2032-11-07","2032-11-22","2032-12-06","2032-12-21"
    ], []),
    2033: ([
        "2033-01-05","2033-01-20","2033-02-03","2033-02-18",
        "2033-03-05","2033-03-20","2033-04-04","2033-04-20",
        "2033-05-05","2033-05-21","2033-06-05","2033-06-21",
        "2033-07-07","2033-07-22","2033-08-07","2033-08-23",
        "2033-09-07","2033-09-23","2033-10-08","2033-10-23",
        "2033-11-07","2033-11-22","2033-12-07","2033-12-21"
    ], []),
    2034: ([
        "2034-01-05","2034-01-20","2034-02-04","2034-02-18",
        "2034-03-05","2034-03-20","2034-04-05","2034-04-20",
        "2034-05-05","2034-05-21","2034-06-05","2034-06-21",
        "2034-07-07","2034-07-23","2034-08-07","2034-08-23",
        "2034-09-07","2034-09-23","2034-10-08","2034-10-23",
        "2034-11-07","2034-11-22","2034-12-07","2034-12-22"
    ], []),
    2035: ([
        "2035-01-05","2035-01-20","2035-02-04","2035-02-19",
        "2035-03-06","2035-03-21","2035-04-05","2035-04-20",
        "2035-05-05","2035-05-21","2035-06-06","2035-06-21",
        "2035-07-07","2035-07-23","2035-08-07","2035-08-23",
        "2035-09-08","2035-09-23","2035-10-08","2035-10-23",
        "2035-11-07","2035-11-22","2035-12-07","2035-12-22"
    ], []),
    2036: ([
        "2036-01-06","2036-01-20","2036-02-04","2036-02-19",
        "2036-03-05","2036-03-20","2036-04-04","2036-04-19",
        "2036-05-05","2036-05-20","2036-06-05","2036-06-21",
        "2036-07-06","2036-07-22","2036-08-07","2036-08-22",
        "2036-09-07","2036-09-22","2036-10-08","2036-10-23",
        "2036-11-07","2036-11-22","2036-12-06","2036-12-21"
    ], []),
    2037: ([
        "2037-01-05","2037-01-20","2037-02-03","2037-02-18",
        "2037-03-05","2037-03-20","2037-04-04","2037-04-20",
        "2037-05-05","2037-05-21","2037-06-05","2037-06-21",
        "2037-07-07","2037-07-22","2037-08-07","2037-08-23",
        "2037-09-07","2037-09-23","2037-10-08","2037-10-23",
        "2037-11-07","2037-11-22","2037-12-07","2037-12-21"
    ], []),
    2038: ([
        "2038-01-05","2038-01-20","2038-02-04","2038-02-18",
        "2038-03-05","2038-03-20","2038-04-05","2038-04-20",
        "2038-05-05","2038-05-21","2038-06-05","2038-06-21",
        "2038-07-07","2038-07-23","2038-08-07","2038-08-23",
        "2038-09-07","2038-09-23","2038-10-08","2038-10-23",
        "2038-11-07","2038-11-22","2038-12-07","2038-12-22"
    ], []),
    2039: ([
        "2039-01-05","2039-01-20","2039-02-04","2039-02-19",
        "2039-03-06","2039-03-21","2039-04-05","2039-04-20",
        "2039-05-05","2039-05-21","2039-06-06","2039-06-21",
        "2039-07-07","2039-07-23","2039-08-07","2039-08-23",
        "2039-09-08","2039-09-23","2039-10-08","2039-10-23",
        "2039-11-07","2039-11-22","2039-12-07","2039-12-22"
    ], []),
    2040: ([
        "2040-01-06","2040-01-20","2040-02-04","2040-02-19",
        "2040-03-05","2040-03-20","2040-04-04","2040-04-19",
        "2040-05-05","2040-05-20","2040-06-05","2040-06-21",
        "2040-07-06","2040-07-22","2040-08-07","2040-08-22",
        "2040-09-07","2040-09-22","2040-10-08","2040-10-23",
        "2040-11-07","2040-11-22","2040-12-06","2040-12-21"
    ], []),
    2041: ([
        "2041-01-05","2041-01-20","2041-02-03","2041-02-18",
        "2041-03-05","2041-03-20","2041-04-04","2041-04-20",
        "2041-05-05","2041-05-20","2041-06-05","2041-06-21",
        "2041-07-07","2041-07-22","2041-08-07","2041-08-23",
        "2041-09-07","2041-09-22","2041-10-08","2041-10-23",
        "2041-11-07","2041-11-22","2041-12-07","2041-12-21"
    ], []),
    2042: ([
        "2042-01-05","2042-01-20","2042-02-04","2042-02-18",
        "2042-03-05","2042-03-20","2042-04-04","2042-04-20",
        "2042-05-05","2042-05-21","2042-06-05","2042-06-21",
        "2042-07-07","2042-07-23","2042-08-07","2042-08-23",
        "2042-09-07","2042-09-23","2042-10-08","2042-10-23",
        "2042-11-07","2042-11-22","2042-12-07","2042-12-22"
    ], []),
    2043: ([
        "2043-01-05","2043-01-20","2043-02-04","2043-02-19",
        "2043-03-06","2043-03-21","2043-04-05","2043-04-20",
        "2043-05-05","2043-05-21","2043-06-06","2043-06-21",
        "2043-07-07","2043-07-23","2043-08-07","2043-08-23",
        "2043-09-08","2043-09-23","2043-10-08","2043-10-23",
        "2043-11-07","2043-11-22","2043-12-07","2043-12-22"
    ], []),
    2044: ([
        "2044-01-06","2044-01-20","2044-02-04","2044-02-19",
        "2044-03-05","2044-03-20","2044-04-04","2044-04-19",
        "2044-05-05","2044-05-20","2044-06-05","2044-06-21",
        "2044-07-06","2044-07-22","2044-08-07","2044-08-22",
        "2044-09-07","2044-09-22","2044-10-07","2044-10-23",
        "2044-11-07","2044-11-22","2044-12-06","2044-12-21"
    ], []),
    2045: ([
        "2045-01-05","2045-01-20","2045-02-03","2045-02-18",
        "2045-03-05","2045-03-20","2045-04-04","2045-04-19",
        "2045-05-05","2045-05-20","2045-06-05","2045-06-21",
        "2045-07-07","2045-07-22","2045-08-07","2045-08-23",
        "2045-09-07","2045-09-22","2045-10-08","2045-10-23",
        "2045-11-07","2045-11-22","2045-12-07","2045-12-21"
    ], []),
    2046: ([
        "2046-01-05","2046-01-20","2046-02-04","2046-02-18",
        "2046-03-05","2046-03-20","2046-04-04","2046-04-20",
        "2046-05-05","2046-05-21","2046-06-05","2046-06-21",
        "2046-07-07","2046-07-22","2046-08-07","2046-08-23",
        "2046-09-07","2046-09-23","2046-10-08","2046-10-23",
        "2046-11-07","2046-11-22","2046-12-07","2046-12-22"
    ], []),
    2047: ([
        "2047-01-05","2047-01-20","2047-02-04","2047-02-19",
        "2047-03-06","2047-03-21","2047-04-05","2047-04-20",
        "2047-05-05","2047-05-21","2047-06-06","2047-06-21",
        "2047-07-07","2047-07-23","2047-08-07","2047-08-23",
        "2047-09-08","2047-09-23","2047-10-08","2047-10-23",
        "2047-11-07","2047-11-22","2047-12-07","2047-12-22"
    ], []),
    2048: ([
        "2048-01-06","2048-01-20","2048-02-04","2048-02-19",
        "2048-03-05","2048-03-20","2048-04-04","2048-04-19",
        "2048-05-05","2048-05-20","2048-06-05","2048-06-20",
        "2048-07-06","2048-07-22","2048-08-07","2048-08-22",
        "2048-09-07","2048-09-22","2048-10-07","2048-10-23",
        "2048-11-07","2048-11-21","2048-12-06","2048-12-21"
    ], []),
    2049: ([
        "2049-01-05","2049-01-19","2049-02-03","2049-02-18",
        "2049-03-05","2049-03-20","2049-04-04","2049-04-19",
        "2049-05-05","2049-05-20","2049-06-05","2049-06-21",
        "2049-07-06","2049-07-22","2049-08-07","2049-08-22",
        "2049-09-07","2049-09-22","2049-10-08","2049-10-23",
        "2049-11-07","2049-11-22","2049-12-07","2049-12-21"
    ], []),
    2050: ([
        "2050-01-05","2050-01-20","2050-02-03","2050-02-18",
        "2050-03-05","2050-03-20","2050-04-04","2050-04-20",
        "2050-05-05","2050-05-21","2050-06-05","2050-06-21",
        "2050-07-07","2050-07-22","2050-08-07","2050-08-23",
        "2050-09-07","2050-09-23","2050-10-08","2050-10-23",
        "2050-11-07","2050-11-22","2050-12-07","2050-12-22"
    ], [])
}

solar_terms_cache = {}

def get_solar_terms(year):
    if year in solar_terms_cache:
        return solar_terms_cache[year]
    
    if year not in jieqi_table:
        raise ValueError(f"{year} 年的節氣資料不存在")

    solar_dates_str = jieqi_table[year][0]
    results = {}
    for i, date_str in enumerate(solar_dates_str):
        term_name = jieqi_names[i]
        results[term_name] = datetime.strptime(date_str, "%Y-%m-%d")
            
    solar_terms_cache[year] = results
    return results

# --- 焦氏直日卦計算 ---

term_hex = {
    "立春": ["小過", "蒙", "益", "漸", "泰"],
    "驚蟄": ["需", "隨", "晉", "解", "大壯"],
    "清明": ["豫", "訟", "蠱", "革", "夬"],
    "立夏": ["旅", "師", "比", "小畜", "乾"],
    "芒種": ["大有", "家人", "井", "咸", "姤"],
    "小暑": ["鼎", "豐", "渙", "履", "遯"],
    "立秋": ["恒", "節", "同人", "損", "否"],
    "白露": ["巽", "萃", "大畜", "賁", "觀"],
    "寒露": ["歸妹", "無妄", "明夷", "困", "剝"],
    "立冬": ["艮", "既濟", "噬嗑", "大過", "坤"],
    "大雪": ["未濟", "蹇", "頤", "中孚", "復"],
    "小寒": ["屯", "謙", "睽", "升", "臨"]
}

SPECIAL_HEX_DAYS = {
    "春分": "震",
    "夏至": "離",
    "秋分": "兌",
    "冬至": "坎"
}

def get_hex(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    year = date.year

    try:
        solar_terms_data = get_solar_terms(year)
    except Exception as e:
        return f"無法計算節氣: {e}", None

    # 檢查是否為四正卦日
    for term_name, hex_name in SPECIAL_HEX_DAYS.items():
        if term_name in solar_terms_data and solar_terms_data[term_name].date() == date:
            return hex_name, term_name

    # 找出當前日期所在的節氣區間
    period_start_term_name = None
    period_start_date = None

    jie_terms = {name: dt for name, dt in solar_terms_data.items() if name in term_hex}
    sorted_jie_terms = sorted(jie_terms.items(), key=lambda item: item[1])
    
    for name, dt in sorted_jie_terms:
        if dt.date() <= date:
            period_start_term_name = name
            period_start_date = dt
        else:
            break

    if period_start_term_name is None:
        # This handles dates at the beginning of the year that belong to the previous year's last solar term period
        last_year_terms = get_solar_terms(year - 1)
        if "小寒" in last_year_terms and last_year_terms["小寒"].date() <= date:
            period_start_term_name = "小寒"
            period_start_date = last_year_terms["小寒"]
        elif "大雪" in last_year_terms and last_year_terms["大雪"].date() <= date:
            period_start_term_name = "大雪"
            period_start_date = last_year_terms["大雪"]
        else:
            return "無法確定年初的節氣區間", None

    if not period_start_date:
        return "無法確定節氣區間", None

    day_diff = (date - period_start_date.date()).days

    special_term_in_period = None
    if period_start_term_name == "驚蟄":
        special_term_in_period = "春分"
    elif period_start_term_name == "芒種":
        special_term_in_period = "夏至"
    elif period_start_term_name == "白露":
        special_term_in_period = "秋分"
    elif period_start_term_name == "大雪":
        special_term_in_period = "冬至"

    if special_term_in_period and date > solar_terms_data[special_term_in_period].date():
        day_diff -= 1

    hex_list = term_hex[period_start_term_name]
    hex_index = day_diff // 6
    
    if hex_index >= len(hex_list):
        hex_index = len(hex_list) - 1

    return hex_list[hex_index], period_start_term_name

# --- 資料處理函式 ---

def parse_sql_file():
    """解析 yilin.sql 檔案並回傳資料結構"""
    if not os.path.exists(SQL_FILE_PATH):
        return []
    
    with open(SQL_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    data = []
    insert_pattern = re.compile(r"INSERT INTO yilin \(from_hexagram, to_hexagram, verse\) VALUES \('(.*?)', '(.*?)', '(.*?)'\);", re.DOTALL)
    
    matches = insert_pattern.findall(content)
    for match in matches:
        data.append({
            'from': match[0].strip(),
            'to': match[1].strip(),
            'verse': match[2].replace("''", "'").strip()
        })
    return data

def write_sql_file(data):
    """將資料寫回 yilin.sql 檔案"""
    with open(SQL_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write("CREATE TABLE yilin (\n")
        f.write("    from_hexagram TEXT,\n")
        f.write("    to_hexagram TEXT,\n")
        f.write("    verse TEXT\n")
        f.write(");\n\n")
        for entry in data:
            verse_escaped = entry['verse'].replace("'", "''")
            f.write(f"INSERT INTO yilin (from_hexagram, to_hexagram, verse) VALUES ('{entry['from']}', '{entry['to']}', '{verse_escaped}');\n")

# --- 卦象資料 ---

HEX_INFO = {
    "乾": {"number": "01", "symbol": "䷀"}, "坤": {"number": "02", "symbol": "䷁"},
    "屯": {"number": "03", "symbol": "䷂"}, "蒙": {"number": "04", "symbol": "䷃"},
    "需": {"number": "05", "symbol": "䷄"}, "訟": {"number": "06", "symbol": "䷅"},
    "師": {"number": "07", "symbol": "䷆"}, "比": {"number": "08", "symbol": "䷇"},
    "小畜": {"number": "09", "symbol": "䷈"}, "履": {"number": "10", "symbol": "䷉"},
    "泰": {"number": "11", "symbol": "䷊"}, "否": {"number": "12", "symbol": "䷋"},
    "同人": {"number": "13", "symbol": "䷌"}, "大有": {"number": "14", "symbol": "䷍"},
    "謙": {"number": "15", "symbol": "䷎"}, "豫": {"number": "16", "symbol": "䷏"},
    "隨": {"number": "17", "symbol": "䷐"}, "蠱": {"number": "18", "symbol": "䷑"},
    "臨": {"number": "19", "symbol": "䷒"}, "觀": {"number": "20", "symbol": "䷓"},
    "噬嗑": {"number": "21", "symbol": "䷔"}, "賁": {"number": "22", "symbol": "䷕"},
    "剝": {"number": "23", "symbol": "䷖"}, "復": {"number": "24", "symbol": "䷗"},
    "無妄": {"number": "25", "symbol": "䷘"}, "大畜": {"number": "26", "symbol": "䷙"},
    "頤": {"number": "27", "symbol": "䷚"}, "大過": {"number": "28", "symbol": "䷛"},
    "坎": {"number": "29", "symbol": "䷜"}, "離": {"number": "30", "symbol": "䷝"},
    "咸": {"number": "31", "symbol": "䷞"}, "恒": {"number": "32", "symbol": "䷟"},
    "遯": {"number": "33", "symbol": "䷠"}, "大壯": {"number": "34", "symbol": "䷡"},
    "晉": {"number": "35", "symbol": "䷢"}, "明夷": {"number": "36", "symbol": "䷣"},
    "家人": {"number": "37", "symbol": "䷤"}, "睽": {"number": "38", "symbol": "䷥"},
    "蹇": {"number": "39", "symbol": "䷦"}, "解": {"number": "40", "symbol": "䷧"},
    "損": {"number": "41", "symbol": "䷨"}, "益": {"number": "42", "symbol": "䷩"},
    "夬": {"number": "43", "symbol": "䷪"}, "姤": {"number": "44", "symbol": "䷫"},
    "萃": {"number": "45", "symbol": "䷬"}, "升": {"number": "46", "symbol": "䷭"},
    "困": {"number": "47", "symbol": "䷮"}, "井": {"number": "48", "symbol": "䷯"},
    "革": {"number": "49", "symbol": "䷰"}, "鼎": {"number": "50", "symbol": "䷱"},
    "震": {"number": "51", "symbol": "䷲"}, "艮": {"number": "52", "symbol": "䷳"},
    "漸": {"number": "53", "symbol": "䷴"}, "歸妹": {"number": "54", "symbol": "䷵"},
    "豐": {"number": "55", "symbol": "䷶"}, "旅": {"number": "56", "symbol": "䷷"},
    "巽": {"number": "57", "symbol": "䷸"}, "兌": {"number": "58", "symbol": "䷹"},
    "渙": {"number": "59", "symbol": "䷺"}, "節": {"number": "60", "symbol": "䷻"},
    "中孚": {"number": "61", "symbol": "䷼"}, "小過": {"number": "62", "symbol": "䷽"},
    "既濟": {"number": "63", "symbol": "䷾"}, "未濟": {"number": "64", "symbol": "䷿"}
}

# --- HTML 模板 ---

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>焦氏易林編輯器</title>
    <style>
        body { font-family: sans-serif; margin: 2em; background: #f9f9f9; }
        h1 { color: #333; text-align: center; }
        .nav-link { margin-bottom: 1em; text-align: center; font-size: 1.2em;}
        ul {
            list-style: none;
            padding: 0;
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
        }
        li {
            flex: 0 0 11.5%; /* 8 items per row */
            box-sizing: border-box;
            margin: 5px;
            padding: 10px;
            background: #fff;
            border: 1px solid #ddd;
            border-radius: 5px;
            text-align: center;
        }
        a { text-decoration: none; color: #0066cc; }
        a:hover { background-color: #f0f0f0; }
        .hex-name { font-size: 1.2em; margin-bottom: 5px; }
        .hex-symbol { font-size: 2em; line-height: 1; }
    </style>
</head>
<body>
    <h1>焦氏易林編輯器 - 選擇起始卦</h1>
    <div class="nav-link"><a href="{{ url_for('fate_calculator') }}">前往焦氏直日卦計算機</a></div>
    <ul>
        {% for hexagram_name in from_hexagrams %}
        <li>
            <a href="{{ url_for('hexagram_details', from_hex=hexagram_name) }}">
                <div class="hex-name">{{ hex_info[hexagram_name].number }}. {{ hexagram_name }}</div>
                <div class="hex-symbol">{{ hex_info[hexagram_name].symbol }}</div>
            </a>
        </li>
        {% endfor %}
    </ul>
</body>
</html>
'''

DETAILS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>卦辭 - {{ from_hex }}</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-top: 1em;}
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        a { color: #0066cc; }
        .flash { background: #cee5F5; padding: 0.5em; border: 1px solid #aacbe2; margin-bottom: 1em; }
        .self-verse { background-color: #fffbe6; border: 1px solid #ffe58f; padding: 1em; margin-bottom: 1em; border-radius: 5px; }
    </style>
</head>
<body>
    <a href="{{ url_for('index') }}">&larr; 返回主頁</a>
    <h1>{{ from_hex }}</h1>

    {% if self_verse_entry %}
    <div class="self-verse">
        <h2>{{ self_verse_entry.from }} 之 {{ self_verse_entry.to }}</h2>
        <p>{{ self_verse_entry.verse }}</p>
        <a href="{{ url_for('edit_verse', from_hex=from_hex, to_hex=self_verse_entry.to) }}">編輯</a>
    </div>
    {% endif %}

    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class=flash>{{ messages[0] }}</div>
      {% endif %}
    {% endwith %}

    <h2>其他變卦</h2>
    <table>
        <tr>
            <th>變卦</th>
            <th>卦辭</th>
            <th>操作</th>
        </tr>
        {% for entry in verses %}
        <tr>
            <td>{{ entry.to }}</td>
            <td>{{ entry.verse }}</td>
            <td><a href="{{ url_for('edit_verse', from_hex=from_hex, to_hex=entry.to) }}">編輯</a></td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
'''

EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>編輯卦辭</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        h1 { color: #333; }
        textarea { width: 100%; height: 200px; font-size: 1em; padding: 5px; }
        input[type="submit"] { padding: 10px 15px; background: #0066cc; color: white; border: none; cursor: pointer; }
    </style>
</head>
<body>
    <a href="{{ url_for('hexagram_details', from_hex=from_hex) }}">&larr; 返回</a>
    <h1>編輯: {{ from_hex }} 之 {{ to_hex }}</h1>
    <form method="post">
        <textarea name="verse">{{ verse }}</textarea>
        <br><br>
        <input type="submit" value="儲存變更">
    </form>
</body>
</html>
'''

FATE_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <title>焦氏直日卦計算機</title>
    <style>
        body { font-family: sans-serif; margin: 2em; }
        h1 { color: #333; }
        .flash { background: #cee5F5; padding: 0.5em; border: 1px solid #aacbe2; margin-bottom: 1em; }
        a { color: #0066cc; }
    </style>
</head>
<body>
    <a href="{{ url_for('index') }}">&larr; 返回主頁</a>
    <h1>焦氏直日卦計算機</h1>
    <form method="post">
        <label for="date">請輸入日期 (YYYY-MM-DD)，留空則使用今天日期：</label>
        <input type="text" id="date" name="date" value="{{ input_date or '' }}">
        <input type="submit" value="計算">
    </form>
    {% if result and solar_term %}
    <h2>結果</h2>
    <p>日期: {{ input_date }}</p>
    <p>節氣: {{ solar_term }}</p>
    <p>焦氏直日卦為： <a href="{{ url_for('hexagram_details', from_hex=result) }}">{{ result }}</a></p>
    {% elif result %}
    <h2>結果</h2>
    <p>{{ result }}</p>
    {% endif %}
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class=flash>{{ messages[0] }}</div>
      {% endif %}
    {% endwith %}
</body>
</html>
'''


# --- Flask 路由 ---

@app.route('/')
def index():
    data = parse_sql_file()
    from_hexagrams = list(set(entry['from'] for entry in data))
    
    HEX_ORDER = [
        "乾", "坤", "屯", "蒙", "需", "訟", "師", "比", "小畜", "履", "泰", "否", 
        "同人", "大有", "謙", "豫", "隨", "蠱", "臨", "觀", "噬嗑", "賁", 
        "剝", "復", "無妄", "大畜", "頤", "大過", "坎", "離", "咸", "恒", "遯", 
        "大壯", "晉", "明夷", "家人", "睽", "蹇", "解", "損", "益", "夬", "姤", 
        "萃", "升", "困", "井", "革", "鼎", "震", "艮", "漸", "歸妹", "豐", 
        "旅", "巽", "兌", "渙", "節", "中孚", "小過", "既濟", "未濟"
    ]

    order_map = {hex_name: i for i, hex_name in enumerate(HEX_ORDER)}
    from_hexagrams.sort(key=lambda x: order_map.get(x, len(HEX_ORDER)))
    
    return render_template_string(INDEX_TEMPLATE, from_hexagrams=from_hexagrams, hex_info=HEX_INFO)

@app.route('/hexagram/<from_hex>')
def hexagram_details(from_hex):
    data = parse_sql_file()
    
    self_verse_entry = None
    other_verses = []
    for entry in data:
        if entry['from'] == from_hex:
            if entry['to'] == from_hex:
                self_verse_entry = entry
            else:
                other_verses.append(entry)

    return render_template_string(DETAILS_TEMPLATE, 
                                  from_hex=from_hex, 
                                  self_verse_entry=self_verse_entry, 
                                  verses=other_verses)

@app.route('/edit/<from_hex>/<to_hex>', methods=['GET', 'POST'])
def edit_verse(from_hex, to_hex):
    data = parse_sql_file()
    entry_to_edit = None
    entry_index = -1
    for i, entry in enumerate(data):
        if entry['from'] == from_hex and entry['to'] == to_hex:
            entry_to_edit = entry
            entry_index = i
            break

    if entry_to_edit is None:
        return "找不到指定的卦辭", 404

    if request.method == 'POST':
        new_verse = request.form['verse']
        data[entry_index]['verse'] = new_verse
        write_sql_file(data)
        flash(f"已成功更新 '{from_hex} 之 {to_hex}' 的卦辭。")
        return redirect(url_for('hexagram_details', from_hex=from_hex))

    return render_template_string(EDIT_TEMPLATE, from_hex=from_hex, to_hex=to_hex, verse=entry_to_edit['verse'])

@app.route('/fate', methods=['GET', 'POST'])
def fate_calculator():
    result = None
    solar_term = None
    input_date = datetime.now().strftime("%Y-%m-%d")

    if request.method == 'POST':
        input_date = request.form.get('date')
        if not input_date:
            input_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            datetime.strptime(input_date, "%Y-%m-%d")
            result, solar_term = get_hex(input_date)
        except ValueError:
            flash("日期格式錯誤，請使用 YYYY-MM-DD 格式。")
            return render_template_string(FATE_TEMPLATE, result=None, solar_term=None, input_date=input_date)
        except Exception as e:
            flash(str(e))
            return render_template_string(FATE_TEMPLATE, result=None, solar_term=None, input_date=input_date)

    return render_template_string(FATE_TEMPLATE, result=result, solar_term=solar_term, input_date=input_date)


if __name__ == '__main__':
    if not os.path.exists(SQL_FILE_PATH):
        print(f"錯誤：找不到 SQL 檔案 '{SQL_FILE_PATH}'。請先確定檔案存在於與 app.py 相同的目錄中。")
    else:
        print("啟動 Flask 伺服器...")
        print(f"請在您的瀏覽器中開啟 http://127.0.0.1:5000")
        app.run(debug=True)
