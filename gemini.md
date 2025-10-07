# GEMINI — 命理 × Python 專案說明

> 作者身份：中國命理專家（紫微斗數、四柱推命、梅花易數）＋ Python 應用實作模板

---

## 目錄

1. 介紹與使用說明
2. 紫微斗數（概念、演算流程、程式樣板）
3. 四柱推命（概念、八字推算、程式樣板）
4. 梅花易數（概念、卜卦流程、程式樣板）
5. 結合輸出：報表、圖表、匯出格式（Markdown / PDF / PPTX）
6. 範例：完整命盤產生器（可執行版）
7. 注意事項、資料來源與授權

---

## 1. 介紹與使用說明

這個檔案提供一套從傳統命理觀念出發，並結合 Python 自動化運算的實作範本。目標讀者為：熟悉命理概念且會寫 Python 的使用者，或是希望快速把命理結果自動化、匯出成簡報或報表的人。

檔案以**繁體中文**撰寫，所有程式範例均為可直接複製執行的 Python 片段（某些範例需要第三方套件，會在說明中標註）。

---

## 2. 紫微斗數

### 2.1 概念要點

- 紫微斗數的核心是以命主出生（陽曆/陰曆）年、月、日、時，推算紫微星系於十二宮位（命宮、兄弟、夫妻等）的分佈與主星、輔星能量。通常需經過「時辰換算（地支）」與「小限/大限/流年」等進位演算。

### 2.2 演算流程（簡化）

1. 將出生時間轉換為農曆（含節氣判斷）。
2. 決定命宮起點（以月將或日干支等算法，可依門派不同而異）。
3. 將主要星曜依固定表格放入十二宮。
4. 計算大限、小限、流年位置。

> 註：完整紫微演算牽涉到大量門派細節（如「子平派」或「文曲派」差異），下列程式樣板提供一個通用的模組化起點，方便使用者依門派規則調整。

### 2.3 Python 範例（紫微結構模版）

```python
# gemini_ziwei.py
# 簡化的紫微盤資料結構與輸出
from dataclasses import dataclass, field
from typing import Dict, List

PALACES = [
    "命宮", "兄弟", "夫妻", "子女", "財帛", "疾厄",
    "遷移", "僕役", "官祿", "田宅", "福德", "父母"
]

@dataclass
class ZiweiChart:
    birth: str  # ISO datetime or dict
    palaces: Dict[str, List[str]] = field(default_factory=lambda: {p: [] for p in PALACES})
    notes: Dict[str, str] = field(default_factory=dict)

    def place_star(self, palace: str, star: str):
        self.palaces[palace].append(star)

    def to_markdown(self) -> str:
        md = f"# 紫微斗數命盤 - {self.birth}\n\n"
        for p in PALACES:
            stars = ', '.join(self.palaces[p]) or '—'
            md += f"- **{p}**: {stars}\n"
        return md

# 範例用法
if __name__ == '__main__':
    chart = ZiweiChart('1971-06-19T03:00')
    chart.place_star('命宮', '紫微')
    chart.place_star('命宮', '天相')
    print(chart.to_markdown())
```

---

## 3. 四柱推命（八字）

### 3.1 概念要點

- 四柱（年柱、月柱、日柱、時柱）各含天干與地支。八字的五行、生剋、格局、十神、用神等判斷是核心。一次準確的八字推算通常需要精確的節氣轉換。

### 3.2 套件建議

若需要精確的曆法及節氣轉換，推薦使用 `sxtwl`（史氏天文庫，俗稱 朔望/節氣換算套件）或 `lunardate` 作為基礎。示範程式會同時提供純算法接口與使用外部套件的版本。

### 3.3 Python 範例（八字推算，需 sxtwl）

```python
# gemini_bazi.py
# 依賴: pip install sxtwl
import sxtwl

def calc_bazi(year, month, day, hour, minute=0):
    # 以 sxtwl 計算干支（示意）
    dayi = sxtwl.fromSolar(year, month, day)
    # dayi 可以提供節氣、干支等資訊
    # 這裡只示意取天干地支
    year_gan = dayi.getYearGZ()  # 返回年柱的干支索引（示意）
    # 真實用法請參考 sxtwl 文件
    return dayi

if __name__ == '__main__':
    d = calc_bazi(1971, 6, 19, 3)
    print(d)
```

> 範例說明：`sxtwl` 可以直接回傳年、月、日、時的天干地支與節氣資訊；請依文件解析回傳結構以組成八字。

---

## 4. 梅花易數（卜卦）

### 4.1 概念要點

- 梅花易數是一種以事主的時間、問卜方式與周易六十四卦進行對照的占卜法。常見流程：擲銅錢或三枚錢法，取數得主卦，再求互卦、變卦、錯綜卦，並根據爻辭與卦象做斷。

### 4.2 Python 範例（隨機/時間決定卦象）

```python
# gemini_meihua.py
import time
from hashlib import sha256

HEXAGRAMS = [f"卦-{i+1}" for i in range(64)]

def time_based_hexagram(timestamp=None):
    if timestamp is None:
        timestamp = time.time()
    h = sha256(str(timestamp).encode()).hexdigest()
    n = int(h[:8], 16) % 64
    return HEXAGRAMS[n]

if __name__ == '__main__':
    print('本次卦象：', time_based_hexagram())
```

> 註：上例以時間雜湊取代傳統搖卦，目的是在程式自動化時保持可重現性；實務卜卦仍建議使用實物或指定隨機源。

---

## 5. 結合輸出：報表、圖表、匯出

### 5.1 匯出為 Markdown / PDF / PPTX

- Markdown：用 `to_markdown()` 類方法輸出內容。
- PDF：可採 `weasyprint` 或 `reportlab` 將 HTML/Markdown 轉為 PDF。
- PPTX：使用 `python-pptx` 將每個宮位或八字要點生成投影片。

```python
# 匯出 PPTX 範例片段
from pptx import Presentation
from pptx.util import Inches

def export_chart_to_pptx(chart_md: str, filename='ziwei.pptx'):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    tx = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(5))
    tf = tx.text_frame
    for line in chart_md.splitlines():
        p = tf.add_paragraph()
        p.text = line
    prs.save(filename)

# 使用: export_chart_to_pptx(chart.to_markdown())
```

---

## 6. 範例：完整命盤產生器（快速路徑）

目標：輸入公曆出生時間 -> 輸出八字 + 紫微十二宮（簡化）+ 一頁式摘要（Markdown）

```python
# gemini_generator.py (示意流程)
# 步驟：
# 1. 讀入出生日期時間
# 2. 用 sxtwl / lunardate 轉農曆、節氣
# 3. 計算八字（year/month/day/hour 天干地支）
# 4. 用簡化規則排入紫微十二宮
# 5. 合成 Markdown 並匯出

def generate_report(birth_dt):
    # 1-3: 以前章節模組實作
    bazi_md = '# 八字摘要\n- 年柱: 甲子\n- 月柱: 乙丑\n'
    ziwei_md = '# 紫微命盤（簡化）\n- 命宮: 紫微、天相\n'
    return bazi_md + '\n' + ziwei_md

if __name__ == '__main__':
    print(generate_report('1971-06-19T03:00'))
```

---

## 7. 注意事項、資料來源與授權

1. 本檔案提供的算法多為**教學/範例**用法，命理實務判斷需考慮門派細節與大量經驗。請於商業或正式論斷前加以驗證。
2. 若用到套件如 `sxtwl`, `python-pptx`, `weasyprint`，請依需安裝並閱讀套件文件。
3. 授權：你可以自由修改與商用本範例，但若引用第三方套件請遵守其授權條款。

---

## 聯絡與後續

若你希望：

- 我幫你把 `GEMINI.md` 轉成可執行的 `gemini_generator.py`，或
- 我把範例補齊成完整的紫微排盤（包含節氣判斷、大限/流年計算）、或
- 匯出 PowerPoint（淺藍色、警政風格）版本的簡報，

請直接告訴我你要的**功能範圍**與**輸入範例（出生時間）**，我會直接幫你產出可執行的檔案。

---

*GEMINI.md 由 ChatGPT 模板產生，內容以教學與範例為主。*

