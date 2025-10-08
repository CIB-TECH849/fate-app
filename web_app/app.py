# app.py (v4 - Admin Panel)

import os
import sys
import datetime
from typing import List, Tuple, Dict
from functools import wraps

import google.generativeai as genai
from flask import (Flask, render_template, request, session, redirect, 
                   url_for, flash)
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from markdown_it import MarkdownIt

# --- 將專案根目錄添加到 Python 路徑中 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))
import gemini_meihua_module as meihua

# --- Flask App 初始化與設定 ---
app = Flask(__name__)

# --- API 與應用程式設定 ---
api_key_error_message = ""
try:
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if not app.config['SECRET_KEY'] or not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("錯誤：找不到 SECRET_KEY 或 DATABASE_URL 環境變數。")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("錯誤：在 Render 環境變數中找不到 GEMINI_API_KEY。")
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

# --- 核心功能函式 (無變動) ---
def calculate_hexagram(num1: int, num2: int, num3: int) -> Tuple[List[int], int]:
    # ... (此處程式碼與之前版本相同，為節省篇幅省略)
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
    # ... (此處程式碼與之前版本相同，為節省篇幅省略)
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
    # ... (此處程式碼與之前版本相同，為節省篇幅省略)
    try:
        model = genai.GenerativeModel('models/gemini-pro-latest')
        response = model.generate_content(prompt)
        md = MarkdownIt()
        html = md.render(response.text)
        return Markup(html)
    except Exception as e:
        return f"<p>呼叫 Gemini API 時出錯：</p><p>{e}</p>"

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
    # 只在沒有任何使用者時才開放註冊
    if User.query.first() is not None:
        flash('註冊功能已關閉。', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        # 第一個註冊的使用者，其 ID 將為 1，自動成為管理員
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('管理員帳號註冊成功！請登入。', 'success')
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
        new_count = int(request.form.get('count'))
        if new_count >= 0:
            user.usage_count = new_count
            db.session.commit()
            flash(f"會員 {user.username} 的使用次數已更新為 {new_count} 次。", 'success')
        else:
            flash('更新失敗：次數不能為負數。', 'error')
    except (ValueError, TypeError):
        flash('更新失敗：請輸入有效的數字。', 'error')
    return redirect(url_for('admin'))

@app.route("/divine", methods=["POST"])
@login_required
def divine():
    user = User.query.get(session['user_id'])

    # 檢查使用次數 (永久 3 次上限)
    if not user.is_admin and user.usage_count >= 3:
        flash(f'您的占卜次數已達 3 次上限，無法再使用。', 'error')
        return redirect(url_for('index'))

    question = request.form.get("question")
    # ... (後續占卜邏輯與之前相同，為節省篇幅省略)
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

    # 僅在成功解卦後增加計數
    if user and "呼叫 Gemini API 時出錯" not in interpretation_html:
        user.usage_count += 1
        db.session.commit()

    return render_template("result.html", 
                           question=question, 
                           numbers=numbers,
                           hex_data=hex_data,
                           moving_line=moving_line,
                           interpretation=interpretation_html)

# 使用 app context 來建立資料庫表格
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)