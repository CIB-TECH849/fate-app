# -*- coding: utf-8 -*-
import sxtwl
from datetime import datetime
from typing import Dict, List, Tuple

# --- 基礎資料定義 ---
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
SHENGXIAO = ["鼠", "牛", "虎", "兔", "龍", "蛇", "馬", "羊", "猴", "雞", "狗", "豬"]
PALACE_NAMES = [
    "命宮", "兄弟宮", "夫妻宮", "子女宮", "財帛宮", "疾厄宮",
    "遷移宮", "僕役宮", "官祿宮", "田宅宮", "福德宮", "父母宮"
]
ZHI_MAP = {name: i for i, name in enumerate(ZHI)}

# --- 星曜定義 ---
STARS_ZIWEI_GROUP = ["紫微", "天機", "太陽", "武曲", "天同", "廉貞"]
STARS_TIANFU_GROUP = ["天府", "太陰", "貪狼", "巨門", "天相", "天梁", "七殺", "破軍"]
MAIN_STARS = STARS_ZIWEI_GROUP + STARS_TIANFU_GROUP
AUX_STARS_A = ["文昌", "文曲", "左輔", "右弼", "天魁", "天鉞"]

# --- 核心排盤邏輯資料 ---
# 納音五行與五行局 (簡易查詢)
NAYIN_WUXING_TABLE = {
    "甲子": "金", "乙丑": "金", "丙寅": "火", "丁卯": "火", "戊辰": "木", "己巳": "木",
    "庚午": "土", "辛未": "土", "壬申": "金", "癸酉": "金", "甲戌": "火", "乙亥": "火",
    "丙子": "水", "丁丑": "水", "戊寅": "土", "己卯": "土", "庚辰": "金", "辛巳": "金",
    "壬午": "木", "癸未": "木", "甲申": "水", "乙酉": "水", "丙戌": "土", "丁亥": "土",
    "戊子": "火", "己丑": "火", "庚寅": "木", "辛卯": "木", "壬辰": "水", "癸巳": "水",
    "甲午": "金", "乙未": "金", "丙申": "火", "丁酉": "火", "戊戌": "木", "己亥": "木",
    "庚子": "土", "辛丑": "土", "壬寅": "金", "癸卯": "金", "甲辰": "火", "乙巳": "火",
    "丙午": "水", "丁未": "水", "戊申": "土", "己酉": "土", "庚戌": "金", "辛亥": "金",
    "壬子": "木", "癸丑": "木", "甲寅": "水", "乙卯": "水", "丙辰": "土", "丁巳": "土",
    "戊午": "火", "己未": "火", "庚申": "木", "辛酉": "木", "壬戌": "水", "癸亥": "水",
}
WUXING_JU_MAP = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}

# 紫微星位置查詢表: (五行局數, 日期) -> 地支位置
ZIWEI_POS_TABLE = {
    (2, 1): 1, (2, 2): 2, (2, 3): 1, (2, 4): 2, (2, 5): 3, (2, 6): 2, (2, 7): 3, (2, 8): 4, (2, 9): 3, (2, 10): 4,
    (2, 11): 5, (2, 12): 4, (2, 13): 5, (2, 14): 6, (2, 15): 5, (2, 16): 6, (2, 17): 7, (2, 18): 6, (2, 19): 7, (2, 20): 8,
    (2, 21): 7, (2, 22): 8, (2, 23): 9, (2, 24): 8, (2, 25): 9, (2, 26): 10, (2, 27): 9, (2, 28): 10, (2, 29): 11, (2, 30): 10,
    (3, 1): 8, (3, 2): 9, (3, 3): 8, (3, 4): 9, (3, 5): 10, (3, 6): 9, (3, 7): 10, (3, 8): 11, (3, 9): 10, (3, 10): 11,
    (3, 11): 0, (3, 12): 11, (3, 13): 0, (3, 14): 1, (3, 15): 0, (3, 16): 1, (3, 17): 2, (3, 18): 1, (3, 19): 2, (3, 20): 3,
    (3, 21): 2, (3, 22): 3, (3, 23): 4, (3, 24): 3, (3, 25): 4, (3, 26): 5, (3, 27): 4, (3, 28): 5, (3, 29): 6, (3, 30): 5,
    (4, 1): 3, (4, 2): 4, (4, 3): 3, (4, 4): 4, (4, 5): 5, (4, 6): 4, (4, 7): 5, (4, 8): 6, (4, 9): 5, (4, 10): 6,
    (4, 11): 7, (4, 12): 6, (4, 13): 7, (4, 14): 8, (4, 15): 7, (4, 16): 8, (4, 17): 9, (4, 18): 8, (4, 19): 9, (4, 20): 10,
    (4, 21): 9, (4, 22): 10, (4, 23): 11, (4, 24): 10, (4, 25): 11, (4, 26): 0, (4, 27): 11, (4, 28): 0, (4, 29): 1, (4, 30): 0,
    (5, 1): 10, (5, 2): 11, (5, 3): 10, (5, 4): 11, (5, 5): 0, (5, 6): 11, (5, 7): 0, (5, 8): 1, (5, 9): 0, (5, 10): 1,
    (5, 11): 2, (5, 12): 1, (5, 13): 2, (5, 14): 3, (5, 15): 2, (5, 16): 3, (5, 17): 4, (5, 18): 3, (5, 19): 4, (5, 20): 5,
    (5, 21): 4, (5, 22): 5, (5, 23): 6, (5, 24): 5, (5, 25): 6, (5, 26): 7, (5, 27): 6, (5, 28): 7, (5, 29): 8, (5, 30): 7,
    (6, 1): 5, (6, 2): 6, (6, 3): 5, (6, 4): 6, (6, 5): 7, (6, 6): 6, (6, 7): 7, (6, 8): 8, (6, 9): 7, (6, 10): 8,
    (6, 11): 9, (6, 12): 8, (6, 13): 9, (6, 14): 10, (6, 15): 9, (6, 16): 10, (6, 17): 11, (6, 18): 10, (6, 19): 11, (6, 20): 0,
    (6, 21): 11, (6, 22): 0, (6, 23): 1, (6, 24): 0, (6, 25): 1, (6, 26): 2, (6, 27): 1, (6, 28): 2, (6, 29): 3, (6, 30): 2,
}

class BaziChart:
    def __init__(self, year, month, day, hour):
        self.dt = datetime(year, month, day, hour)
        self.day_master = None
        self.pillars = {}
        self._calculate_pillars()

    def _calculate_pillars(self):
        day_obj = sxtwl.fromSolar(self.dt.year, self.dt.month, self.dt.day)
        year_gz = day_obj.getYearGZ()
        self.pillars['year'] = (GAN[year_gz.tg], ZHI[year_gz.dz])
        month_gz = day_obj.getMonthGZ()
        self.pillars['month'] = (GAN[month_gz.tg], ZHI[month_gz.dz])
        day_gz = day_obj.getDayGZ()
        self.pillars['day'] = (GAN[day_gz.tg], ZHI[day_gz.dz])
        self.day_master = GAN[day_gz.tg]
        hour_gz = day_obj.getHourGZ(self.dt.hour)
        self.pillars['hour'] = (GAN[hour_gz.tg], ZHI[hour_gz.dz])

    def to_markdown(self):
        md = "# 八字命盤\n\n"
        md += f"- **陽曆生日**: {self.dt.strftime('%Y-%m-%d %H:%M')}\n"
        md += f"- **日主**: {self.day_master}\n\n"
        md += "| 柱 | 天干 | 地支 |\n|:---:|:---:|:---:|\n"
        md += f"| 年柱 | {self.pillars['year'][0]} | {self.pillars['year'][1]} ({SHENGXIAO[ZHI.index(self.pillars['year'][1])]}) |\n"
        md += f"| 月柱 | {self.pillars['month'][0]} | {self.pillars['month'][1]} |\n"
        md += f"| 日柱 | {self.pillars['day'][0]} | {self.pillars['day'][1]} |\n"
        md += f"| 時柱 | {self.pillars['hour'][0]} | {self.pillars['hour'][1]} |\n"
        return md

class ZiweiChart:
    def __init__(self, year, month, day, hour, gender='male'):
        self.birth_dt = datetime(year, month, day, hour)
        self.gender = gender
        
        lunar_day_obj = sxtwl.fromSolar(year, month, day)
        self.lunar_month = lunar_day_obj.getLunarMonth()
        self.lunar_day = lunar_day_obj.getLunarDay()
        self.year_gan = GAN[lunar_day_obj.getYearGZ().tg]
        self.is_yang_year = lunar_day_obj.getYearGZ().tg % 2 == 0
        
        hour_gz = lunar_day_obj.getHourGZ(hour)
        self.birth_hour_zhi_idx = hour_gz.dz

        self.palaces: Dict[str, Dict] = {name: {"stars": [], "gan": "", "zhi": ""} for name in PALACE_NAMES}
        self.palace_zhi_map: Dict[str, int] = {}
        self.wuxing_ju: Tuple[str, int] = ("", 0)
        self.daxian: List[Dict] = []

        self._setup_palaces()
        self._place_main_stars()
        self._calculate_daxian()

    def _setup_palaces(self):
        # 1. 安命宮、身宮
        ming_palace_zhi_idx = (self.lunar_month - 1 - self.birth_hour_zhi_idx + 12) % 12
        shen_palace_zhi_idx = (self.lunar_month - 1 + self.birth_hour_zhi_idx) % 12
        
        # 2. 安十二宮
        for i in range(12):
            palace_name = PALACE_NAMES[i]
            palace_zhi_idx = (ming_palace_zhi_idx - i + 12) % 12
            self.palace_zhi_map[palace_name] = palace_zhi_idx
            self.palaces[palace_name]["zhi"] = ZHI[palace_zhi_idx]
            if palace_zhi_idx == shen_palace_zhi_idx:
                self.palaces[palace_name]["stars"].append("身宮")

        # 3. 定十二宮天干 (五虎遁)
        gan_start_map = {"甲己": 2, "乙庚": 4, "丙辛": 6, "丁壬": 8, "戊癸": 0}
        start_gan_idx = -1
        for key, val in gan_start_map.items():
            if self.year_gan in key:
                start_gan_idx = val
                break
        
        for i in range(12):
            palace_gan_idx = (start_gan_idx + i) % 10
            palace_zhi_idx = (2 + i) % 12 # 寅宮地支為 2
            for name, idx in self.palace_zhi_map.items():
                if idx == palace_zhi_idx:
                    self.palaces[name]["gan"] = GAN[palace_gan_idx]

    def _place_main_stars(self):
        # 1. 定五行局
        ming_gan = self.palaces["命宮"]["gan"]
        ming_zhi = self.palaces["命宮"]["zhi"]
        nayin_wuxing = NAYIN_WUXING_TABLE.get(ming_gan + ming_zhi, "")
        ju_num = WUXING_JU_MAP.get(nayin_wuxing, 0)
        self.wuxing_ju = (f"{nayin_wuxing}{ju_num}局", ju_num)

        # 2. 安紫微星
        day_for_ziwei = self.lunar_day + (ju_num - (self.lunar_day % ju_num) if self.lunar_day % ju_num != 0 else 0)
        ziwei_zhi_idx = ZIWEI_POS_TABLE.get((ju_num, day_for_ziwei), -1)
        
        # 3. 安紫微星系
        ziwei_stars_pos = [
            (ziwei_zhi_idx, "紫微"),
            ((ziwei_zhi_idx - 1 + 12) % 12, "天機"),
            ((ziwei_zhi_idx - 3 + 12) % 12, "太陽"),
            ((ziwei_zhi_idx - 4 + 12) % 12, "武曲"),
            ((ziwei_zhi_idx - 5 + 12) % 12, "天同"),
            ((ziwei_zhi_idx - 8 + 12) % 12, "廉貞"),
        ]
        for idx, star in ziwei_stars_pos:
            self._add_star_to_palace(idx, star)

        # 4. 安天府星
        tianfu_zhi_idx = (ZHI_MAP["寅"] + ZHI_MAP["戌"] - ziwei_zhi_idx + 12) % 12
        
        # 5. 安天府星系
        self._add_star_to_palace(tianfu_zhi_idx, "天府")
        tf_group_indices = [1, 2, 3, 4, 5, 6, 10] # 貪, 巨, 相, 梁, 殺, -, 破
        tf_stars = ["太陰", "貪狼", "巨門", "天相", "天梁", "七殺", "破軍"]
        
        current_idx = tianfu_zhi_idx
        star_counter = 0
        for i in range(1, 12):
            current_idx = (tianfu_zhi_idx + i) % 12
            if i in tf_group_indices:
                self._add_star_to_palace(current_idx, tf_stars[star_counter])
                star_counter += 1
    
    def _calculate_daxian(self):
        # 定大限起始與方向
        start_age = self.wuxing_ju[1]
        # 陽年出生, 男順女逆; 陰年出生, 男逆女順
        is_clockwise = (self.is_yang_year and self.gender == 'male') or \
                       (not self.is_yang_year and self.gender == 'female')
        
        ming_palace_idx_in_order = PALACE_NAMES.index("命宮")

        for i in range(12):
            age_start = start_age + i * 10
            age_end = age_start + 9
            
            if is_clockwise:
                palace_idx = (ming_palace_idx_in_order + i) % 12
            else:
                palace_idx = (ming_palace_idx_in_order - i + 12) % 12
            
            palace_name = PALACE_NAMES[palace_idx]
            self.daxian.append({
                "palace": palace_name,
                "age_range": f"{age_start}-{age_end}",
                "gan": self.palaces[palace_name]["gan"],
                "zhi": self.palaces[palace_name]["zhi"],
            })

    def _add_star_to_palace(self, zhi_idx: int, star: str):
        for name, p_zhi_idx in self.palace_zhi_map.items():
            if p_zhi_idx == zhi_idx:
                self.palaces[name]["stars"].append(star)
                return

    def to_markdown(self) -> str:
        md = f"# 紫微斗數命盤 (進階版)\n\n"
        md += f"- **基本資訊**: {self.birth_dt.strftime('%Y-%m-%d %H:%M')} ({self.gender}, {'陽' if self.is_yang_year else '陰'}年)\n"
        md += f"- **五行局**: {self.wuxing_ju[0]}\n"
        
        md += "\n## 十二宮盤\n\n"
        for name in PALACE_NAMES:
            p_info = self.palaces[name]
            stars = ', '.join(p_info["stars"]) or "無主星"
            md += f"- **{name} ({p_info['gan']}{p_info['zhi']})**: {stars}\n"
            
        md += "\n## 大限運程\n\n"
        md += "| 宮位 | 大限年齡 | 宮干支 |\n"
        md += "|:---:|:---:|:---:|\n"
        for d in self.daxian:
            md += f"| {d['palace']} | {d['age_range']} | {d['gan']}{d['zhi']} |\n"
            
        md += "\n*注意：此為程式自動排盤，僅供參考。*\n"
        return md

def generate_report(year, month, day, hour, gender='male'):
    bazi = BaziChart(year, month, day, hour)
    ziwei = ZiweiChart(year, month, day, hour, gender)
    
    report_md = f"# 綜合命理報告\n\n"
    report_md += f"## 生日資訊\n- **陽曆**: {year}-{month:02d}-{day:02d} {hour:02d}:00\n"
    report_md += f"- **性別假設**: {gender}\n\n"
    report_md += "---\n\n"
    report_md += bazi.to_markdown()
    report_md += "\n---\n\n"
    report_md += ziwei.to_markdown()
    
    filename = f"report-{year}-{month:02d}-{day:02d}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report_md)
    
    return filename, report_md

if __name__ == '__main__':
    birth_year = 1971
    birth_month = 6
    birth_day = 19
    birth_hour = 3
    
    # 假設為男性，如需女性請更改 'male' -> 'female' 
    assumed_gender = 'male' 
    
    file_name, report_content = generate_report(birth_year, birth_month, birth_day, birth_hour, assumed_gender)
    
    print(f"報告已成功產生並儲存至檔案: {file_name}")
    print("\n--- 報告預覽 ---")
    print(report_content)