# app.py

import os
import sys

# 將專案根目錄添加到 Python 路徑中，以解決 ModuleNotFoundError
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))

import datetime
from typing import List, Tuple, Dict

import google.generativeai as genai
import gemini_meihua_module as meihua
from flask import Flask, render_template, request
from markupsafe import Markup
from markdown_it import MarkdownIt

# --- Flask App Initialization ---
app = Flask(__name__)

# --- API 設定 ---
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("錯誤：請先設定名為 GEMINI_API_KEY 的環境變數。")
    genai.configure(api_key=api_key)
except Exception as e:
    # 在網頁上顯示設定錯誤
    @app.route("/")
    def api_key_error():
        return f"<p>API 金鑰設定錯誤：</p><p>{e}</p><p>請確認您已在環境變數中正確設定 GEMINI_API_KEY。</p>", 500

# --- 核心功能函式 ---

def calculate_hexagram(num1: int, num2: int, num3: int) -> Tuple[List[int], int]:
    """根據三個數字計算卦象和變爻"""
    upper_trigram_num = num1 % 8 or 8
    lower_trigram_num = num2 % 8 or 8
    moving_line_num = num3 % 6 or 6

    trigram_lines_map = {
        1: [1,1,1], 2: [1,1,0], 3: [1,0,1], 4: [1,0,0], # 乾、兌、離、震
        5: [0,1,1], 6: [0,1,0], 7: [0,0,1], 8: [0,0,0]  # 巽、坎、艮、坤
    }
    lines = trigram_lines_map[lower_trigram_num] + trigram_lines_map[upper_trigram_num]
    return lines, moving_line_num

def generate_interpretation_prompt(question: str, numbers: Tuple[int, int, int], hex_data: Dict, moving_line_index: int) -> str:
    """為 Gemini API 生成解卦提示"""
    main_hex = hex_data.get("本卦", {})
    mutual_hex = hex_data.get("互卦", {})
    changing_hex = hex_data.get("變卦", {})
    
    # 取得爻辭，並處理索引錯誤
    try:
        moving_line_text = main_hex.get('lines', [])[moving_line_index - 1]
    except IndexError:
        moving_line_text = "(爻辭資料錯誤或不存在)"

    prompt = f'''
請扮演一位精通《易經》與高島易數風格的解卦專家，為我分析以下卦象：

**1. 我的問題：**
{question}

**2. 起卦資訊：**
- 起卦方式：數字起卦
- 所用數字：{numbers[0]} (上卦), {numbers[1]} (下卦), {numbers[2]} (變爻)
- 動爻：第 {moving_line_index} 爻

**3. 卦象結果：**

*   **本卦：《{main_hex.get('name', '未知')}》**
    *   卦辭：{main_hex.get('judgement', '')}
    *   第 {moving_line_index} 爻爻辭：{moving_line_text}

*   **互卦：《{mutual_hex.get('name', '未知')}》**
    *   卦辭：{mutual_hex.get('judgement', '')}

*   **變卦：《{changing_hex.get('name', '未知')}》**
    *   卦辭：{changing_hex.get('judgement', '')}

請結合我的問題，對「本卦」、「互卦」、「動爻」、「變卦」的關聯與意義進行全面、深入的解讀，並提供具體的結論與建議。
'''
    return prompt

def call_gemini_api(prompt: str) -> str:
    """呼叫 Gemini API 進行解讀"""
    try:
        model = genai.GenerativeModel('models/gemini-pro-latest')
        response = model.generate_content(prompt)
        # 將 Gemini 回傳的 Markdown 文本轉換為 HTML
        md = MarkdownIt()
        html = md.render(response.text)
        return Markup(html)
    except Exception as e:
        return f"<p>呼叫 Gemini API 時出錯：</p><p>{e}</p>"

# --- Flask 路由 ---

@app.route("/")
def index():
    """渲染主輸入頁面"""
    return render_template("index.html")

@app.route("/divine", methods=["POST"])
def divine():
    """處理表單提交並顯示結果"""
    question = request.form.get("question")
    try:
        num1 = int(request.form.get("num1"))
        num2 = int(request.form.get("num2"))
        num3 = int(request.form.get("num3"))
        numbers = (num1, num2, num3)
    except (ValueError, TypeError):
        return "輸入的數字格式錯誤，請返回上一頁修正。", 400

    # 1. 計算卦象
    lines, moving_line = calculate_hexagram(num1, num2, num3)

    # 2. 取得卦象資料
    hex_data = meihua.interpret_hexagrams_from_lines(lines, moving_line)

    # 3. 生成 Prompt
    prompt = generate_interpretation_prompt(question, numbers, hex_data, moving_line)

    # 4. 呼叫 AI 解卦
    interpretation_html = call_gemini_api(prompt)

    # 5. 渲染結果頁面
    return render_template("result.html", 
                           question=question, 
                           numbers=numbers,
                           hex_data=hex_data,
                           moving_line=moving_line,
                           interpretation=interpretation_html)

if __name__ == "__main__":
    # 讓服務在區域網路上可見
    app.run(host='0.0.0.0', port=5000, debug=True)
