# GEMINI — 命理 × Python 專案最終報告

> 本文件記錄了一個從概念到成品的完整 Web 應用程式開發歷程。最終成品是一個功能完善、可部署在雲端的線上梅花易數占卜服務。

---

## 目錄

1.  [專案總覽與最終功能](#1-專案總覽與最終功能)
2.  [技術棧](#2-技術棧)
3.  [專案結構](#3-專案結構)
4.  [設定與執行教學](#4-設定與執行教學)
    - [4.1 環境變數設定 (.env)](#41-環境變數設定-env)
    - [4.2 本地開發模式執行](#42-本地開發模式執行)
    - [4.3 雲端部署 (Render)](#43-雲端部署-render)
5.  [附錄：核心程式碼](#5-附錄核心程式碼)
    - [5.1 app.py](#51-apppy)
    - [5.2 gemini_meihua_module.py](#52-gemini_meihua_modulepy)

---

## 1. 專案總覽與最終功能

本專案從一個本地執行的 Python 腳本開始，逐步迭代，最終成為一個功能完善的線上服務。使用者可以透過網頁介面進行梅花易數占卜，並由管理員在後台進行使用者管理。

**最終實現功能列表：**

*   **網頁介面** ：提供現代化的淺色與深色主題介面，用於占卜、登入、註冊與後台管理。
*   **會員系統** ：
    *   支援多使用者註冊與獨立登入。
    *   第一個註冊的帳號自動成為「管理員」。
    *   支援後續關閉公開註冊，改由管理員在後台手動新增會員。
*   **管理員後台** ：
    *   顯示所有會員列表及其占卜使用次數。
    *   管理員可手動新增、刪除會員。
    *   管理員可手動修改、重設任何會員的占卜次數。
*   **占卜次數限制** ：
    *   普通會員擁有固定的占卜次數上限 (預設為 3 次)。
    *   管理員帳號不受次數限制。
*   **自動郵件通知** ：
    *   每次占卜成功後，系統會自動將該次占卜的完整結果報告，透過 SendGrid 服務寄送到指定信箱。
*   **PDF 報告下載** ：
    *   在占卜結果頁面，提供「下載 PDF 報告」功能，方便使用者本機存放區存。
*   **本地/雲端雙軌制** ：
    *   支援在本機電腦上執行，方便快速開發與測試。
    *   支援一鍵部署到 Render.com 免費雲端平台，供他人公開訪問。

---

## 2. 技術棧

*   **後端框架**: Flask
*   **資料庫**: PostgreSQL (透過 Flask-SQLAlchemy 操作)
*   **會員認證**: Flask-Bcrypt (密碼加密), Flask-Session (狀態管理)
*   **PDF 產生**: fpdf2 (純 Python)
*   **郵件服務**: SendGrid
*   **前端樣式**: 原生 CSS
*   **部署環境**: Gunicorn, Render

---

## 3. 專案結構

```
C:\fate\
├── web_app/                  # Flask 應用程式主目錄
│   ├── templates/            # HTML 模板
│   │   ├── admin.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── result.html
│   └── app.py                # Flask 主程式
├── venv/                     # Python 虛擬環境
├── .env                      # 環境變數檔案 (本地開發用，不上传)
├── .gitignore                # Git 忽略清單
├── Procfile                  # Render 部署啟動指令
├── requirements.txt          # Python 套件依賴列表
├── gemini_meihua_module.py   # 易經核心邏輯模組
├── NotoSansTC-Regular.ttf    # PDF 中文字體檔案
└── ... (其他腳本與文件)
```

---

## 4. 設定與執行教學

### 4.1 環境變數設定 (.env)

在本地執行前，需在專案根目錄 `C:\fate` 建立一個名為 `.env` 的文字檔，內容如下。請將等號後的值換成您自己的真實資訊。

```
# Google Gemini API 金鑰
GEMINI_API_KEY="Your_Gemini_API_Key_Here"

# Render PostgreSQL 資料庫的外部連線網址
DATABASE_URL="Your_External_Database_URL_Here"

# Flask Session 加密用的隨機字串
SECRET_KEY="Your_Own_Random_String_Here"

# SendGrid 的 API 金鑰
SENDGRID_API_KEY="Your_SendGrid_API_Key_Here"

# 普通會員的使用次數上限 (可選)
USAGE_LIMIT="3"
```

### 4.2 本地開發模式執行

1.  確認 `.env` 檔案已正確設定。
2.  在終端機中，進入 `C:\fate` 目錄。
3.  執行指令： `python web_app/app.py`
4.  伺服器啟動後，打開瀏覽器訪問 `http://127.0.0.1:5000`。
5.  修改任何 `.py` 或 `.html` 檔案並存檔後，伺服器會自動重載，只需重新整理瀏覽器即可看到效果。

### 4.3 雲端部署 (Render)

1.  **上傳程式碼** ：將專案透過 `git` 推送到您的 GitHub 倉庫。
2.  **登入 Render** ：訪問 [Render.com](https://render.com) 並建立一個新的 `Web Service`，連接到您的 GitHub 倉庫。
3.  **設定服務** ：
    *   **Runtime**: `Python 3`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn web_app.app:app`
4.  **設定環境變數** ：在 Render 的 `Environment` 頁面，手動加入與 `.env` 檔案中相同的 Key-Value 資訊 (例如 `GEMINI_API_KEY` 和對應的值)。
5.  點擊 `Create Web Service` 完成部署。

---

## 5. 附錄：核心程式碼

### 5.1 app.py

```python
# app.py (v7 - Final Corrected)

import os
from dotenv import load_dotenv

# 在程式的最開始載入 .env 檔案
load_dotenv()

import sys
import datetime
import re
import uuid
from typing import List, Tuple, Dict
from functools import wraps

import google.generativeai as genai
from flask import (
    Flask,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    make_response,
    Response
)
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from markdown_it import MarkdownIt
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

# --- 將專案根目錄添加到 Python 路徑中 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))
import gemini_meihua_module as meihua

# --- Flask App 初始化與設定 ---
app = Flask(__name__)
TEMP_RESULTS = {} # 用於暫存 PDF 資料的記憶體快取

# --- API 與應用程式設定 ---
api_key_error_message = ""
try:
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if not app.config['SECRET_KEY'] or not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("錯誤：找不到 SECRET_KEY 或 DATABASE_URL 環境變數。" )

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("錯誤：在 Render 環境變數中找不到 GEMINI_API_KEY。" )
    
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
    if not sendgrid_api_key:
        raise ValueError("錯誤：在 Render 環境變數中找不到 SENDGRID_API_KEY。" )

    genai.configure(api_key=api_key)

except Exception as e:
    api_key_error_message = str(e)

# --- 資料庫與加密初始化 ---
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# --- 資料庫模型 (User Table) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    usage_count = db.Column(db.Integer, default=0, nullable=False)

    @property
    def is_admin(self):
        return self.id == 1

# --- Decorators for Auth ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            flash('只有管理員才能存取此頁面', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# --- 核心功能函式 ---
def calculate_hexagram(num1: int, num2: int, num3: int) -> Tuple[List[int], int]:
    upper_trigram_num = num1 % 8 or 8
    lower_trigram_num = num2 % 8 or 8
    moving_line_num = num3 % 6 or 6
    trigram_lines_map = {
        1: [1,1,1], 2: [1,1,0], 3: [1,0,1], 4: [1,0,0],
        5: [0,1,1], 6: [0,1,0], 7: [0,0,1], 8: [0,0,0]
    }
    lines = trigram_lines_map[lower_trigram_num] + trigram_lines_map[upper_trigram_num]
    return lines, moving_line_num

def generate_interpretation_prompt(question: str, numbers: Tuple[int, int, int], hex_data: Dict, moving_line_index: int) -> str:
    main_hex = hex_data.get("本卦", {})
    mutual_hex = hex_data.get("互卦", {})
    changing_hex = hex_data.get("變卦", {})
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
    try:
        model = genai.GenerativeModel('models/gemini-pro-latest')
        response = model.generate_content(prompt)
        md = MarkdownIt()
        html = md.render(response.text)
        return Markup(html)
    except Exception as e:
        return f"<p>呼叫 Gemini API 時出錯：</p><p>{e}</p>"

def send_divination_email(question, numbers, hex_data, interpretation_html, user):
    try:
        subject = f"梅花易數占卜結果：{question[:20]}..."
        body_html = f'''
        <html>
        <body style="font-family: sans-serif;">
            <h2>占卜問題：</h2>
            <p>{question}</p>
            <hr>
            <h2>起卦資訊：</h2>
            <ul>
                <li><b>占卜會員：</b> {user['username']}</li>
                <li><b>起卦數字：</b> {numbers[0]} (上), {numbers[1]} (下), {numbers[2]} (爻)</li>
                <li><b>本卦 -> 變卦：</b> {hex_data['本卦'].get('name')} -> {hex_data['變卦'].get('name')}</li>
                <li><b>互卦：</b> {hex_data['互卦'].get('name')}</li>
            </ul>
            <hr>
            <h2>AI 綜合解讀：</h2>
            {interpretation_html}
        </body>
        </html>
        '''
        message = Mail(
            from_email='is33.wu@gmail.com',
            to_emails='is33.wu@gmail.com',
            subject=subject,
            html_content=body_html
        )
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        if not (response.status_code >= 200 and response.status_code < 300):
            flash(f'郵件發送失敗，錯誤碼：{response.status_code}', 'error')
    except Exception as e:
        print(f"Email sending failed: {e}")
        flash(f'郵件發送時發生錯誤: {e}', 'error')

# --- Flask 路由 ---

@app.route("/login", methods=['GET', 'POST'])
def login():
    if api_key_error_message:
        return f'''<h1>應用程式設定錯誤</h1><p>{api_key_error_message}</p>''', 500
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('使用者名稱或密碼錯誤', 'error')
    return render_template('login.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    # This route is now open for public registration
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Add name and phone fields
        name = request.form.get('name')
        phone = request.form.get('phone')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('此使用者名稱已被註冊', 'error')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password_hash=hashed_password, name=name, phone=phone)
        db.session.add(new_user)
        db.session.commit()
        flash('會員帳號註冊成功!請登入', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash('您已成功登出', 'success')
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    if api_key_error_message:
        return f'''<h1>應用程式設定錯誤</h1><p>{api_key_error_message}</p>''', 500
    user = User.query.get(session['user_id'])
    return render_template("index.html", user=user)

@app.route("/admin", methods=['GET', 'POST'])
@admin_required
def admin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('使用者名稱和密碼為必填項', 'error')
        else:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('此使用者名稱已被註冊', 'error')
            else:
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                new_user = User(username=username, password_hash=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                flash(f'會員 {username} 新增成功！', 'success')
        return redirect(url_for('admin'))
    users = User.query.all()
    return render_template("admin.html", users=users)

@app.route("/admin/set_count/<int:user_id>", methods=['POST'])
@admin_required
def set_usage_count(user_id):
    user = User.query.get_or_404(user_id)
    try:
        remaining_count = int(request.form.get('count'))
        if 0 <= remaining_count <= 3:
            user.usage_count = 3 - remaining_count
            db.session.commit()
            flash(f"會員 {user.username} 的剩餘次數已更新為 {remaining_count} 次。", 'success')
        else:
            flash('更新失敗：剩餘次數必須介於 0 到 3 之間。', 'error')
    except (ValueError, TypeError):
        flash('更新失敗：請輸入有效的數字。', 'error')
    return redirect(url_for('admin'))

@app.route("/admin/delete_user/<int:user_id>", methods=['POST'])
@admin_required
def delete_user(user_id):
    user_to_delete = User.query.get_or_404(user_id)
    if user_to_delete.is_admin:
        flash('無法刪除管理員帳號。', 'error')
    else:
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f"會員 {user_to_delete.username} 已被成功刪除。", 'success')
    return redirect(url_for('admin'))

@app.route("/divine", methods=["POST"])
@login_required
def divine():
    user = User.query.get(session['user_id'])
    if not user.is_admin and user.usage_count >= 3:
        flash(f'您的占卜次數已達 3 次上限，無法再使用。', 'error')
        return redirect(url_for('index'))
    question = request.form.get("question")
    try:
        num1 = int(request.form.get("num1"))
        num2 = int(request.form.get("num2"))
        num3 = int(request.form.get("num3"))
        numbers = (num1, num2, num3)
    except (ValueError, TypeError):
        return "輸入的數字格式錯誤，請返回上一頁修正。", 400
    lines, moving_line = calculate_hexagram(num1, num2, num3)
    hex_data = meihua.interpret_hexagrams_from_lines(lines, moving_line)
    prompt = generate_interpretation_prompt(question, numbers, hex_data, moving_line)
    interpretation_html = call_gemini_api(prompt)
    result_id = None
    if user and "呼叫 Gemini API 時出錯" not in interpretation_html:
        user.usage_count += 1
        db.session.commit()
        send_divination_email(question, numbers, hex_data, interpretation_html, {'username': user.username})
        result_id = uuid.uuid4().hex
        TEMP_RESULTS[result_id] = {
            'question': question,
            'numbers': numbers,
            'hex_data': hex_data,
            'interpretation_html': interpretation_html,
            'user': {'username': user.username}
        }
    return render_template("result.html", 
                           question=question, 
                           numbers=numbers,
                           hex_data=hex_data,
                           moving_line=moving_line,
                           interpretation=interpretation_html,
                           result_id=result_id)

@app.route("/download_pdf/<result_id>")
@login_required
def download_pdf(result_id):
    last_result = TEMP_RESULTS.pop(result_id, None)
    if not last_result:
        flash('找不到占卜結果或下載連結已失效。', 'error')
        return redirect(url_for('index'))
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('NotoSansTC', '', 'NotoSansTC-Regular.ttf')
        pdf.set_font('NotoSansTC', '', 16)
        pdf.cell(0, 15, '梅花易數占卜報告', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(10)
        pdf.set_font('NotoSansTC', '', 14)
        pdf.cell(0, 10, '占卜問題：', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('NotoSansTC', '', 12)
        pdf.multi_cell(0, 8, last_result['question'])
        pdf.ln(5)
        pdf.set_font('NotoSansTC', '', 14)
        pdf.cell(0, 10, '起卦資訊：', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('NotoSansTC', '', 12)
        info_text = (
            f"占卜會員： {last_result['user']['username']}\n"
            f"起卦數字： {last_result['numbers'][0]} (上), {last_result['numbers'][1]} (下), {last_result['numbers'][2]} (爻)\n"
            f"本卦 -> 變卦： {last_result['hex_data']['本卦'].get('name')} -> {last_result['hex_data']['變卦'].get('name')}\n"
            f"互卦： {last_result['hex_data']['互卦'].get('name')}"
        )
        pdf.multi_cell(0, 8, info_text)
        pdf.ln(5)
        pdf.set_font('NotoSansTC', '', 14)
        pdf.cell(0, 10, 'AI 綜合解讀：', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font('NotoSansTC', '', 12)
        interpretation_text = re.sub('<[^<]+?>', '', last_result['interpretation_html']).strip()
        pdf.multi_cell(0, 8, interpretation_text)
        pdf_output = pdf.output()
        response = Response(pdf_output, mimetype='application/pdf')
        response.headers['Content-Disposition'] = f'attachment; filename=divination_report_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.pdf'
        return response
    except Exception as e:
        print(f"PDF Generation Error: {e}")
        flash(f'產生 PDF 時發生錯誤: {e}', 'error')
        return redirect(url_for('index'))

# 使用 app context 來建立資料庫表格
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### 5.2 gemini_meihua_module.py

```python
# gemini_meihua_module.py

from typing import List, Dict, Tuple

# 卦象基本資料庫（key為長名）
HEXAGRAM_DB = {
    # ... (64卦的卦辭、爻辭等...)
}

# 將六爻數字轉換為卦名（v5 - 外部驗證版）
HEXAGRAM_MAP = {
    (1, 1, 1, 1, 1, 1): "乾為天",
    (0, 0, 0, 0, 0, 0): "坤為地",
    # ... (其他62卦...)
}

def get_hexagram_from_lines(lines: Tuple[int, ...]) -> str:
    return HEXAGRAM_MAP.get(lines, "未知卦")

def interpret_hexagrams_from_lines(lines: List[int], moving_line_index: int = None) -> Dict[str, Dict]:
    main_hexagram_name = get_hexagram_from_lines(tuple(lines))

    # 計算互卦
    mutual_lines_list = lines[1:4] + lines[2:5]
    mutual_hexagram_name = get_hexagram_from_lines(tuple(mutual_lines_list))

    # 計算變卦
    if moving_line_index is not None and 1 <= moving_line_index <= 6:
        changing_lines = list(lines)
        changing_lines[moving_line_index - 1] = 1 - changing_lines[moving_line_index - 1]
        changing_hexagram_name = get_hexagram_from_lines(tuple(changing_lines))
    else:
        changing_hexagram_name = main_hexagram_name

    def package(name: str) -> Dict:
        data = HEXAGRAM_DB.get(name)
        if data:
            return data
        return {"name": name, "judgement": "未知", "lines": []}

    return {
        "本卦": package(main_hexagram_name),
        "互卦": package(mutual_hexagram_name),
        "變卦": package(changing_hexagram_name)
    }
```