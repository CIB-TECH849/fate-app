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
    Response,
    jsonify,
)
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from markdown_it import MarkdownIt
from fpdf import FPDF
from fpdf.enums import XPos, YPos
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask_cors import CORS

# --- 將專案根目錄添加到 Python 路徑中 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(current_dir))
import gemini_meihua_module as meihua
import liuyao_system as liuyao
import pytz

# Define SQL_FILE_PATH for yilin.sql
SQL_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'yilin.sql')

# --- Flask App 初始化與設定 ---
app = Flask(__name__)
CORS(app) # Enable CORS for all routes and all origins

TAIWAN_TZ = pytz.timezone('Asia/Taipei')

@app.template_filter('to_taiwan_time')
def to_taiwan_time_filter(utc_dt):
    if not utc_dt:
        return ""
    # Ensure the datetime object is timezone-aware UTC
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    return utc_dt.astimezone(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S')

TEMP_RESULTS = {} # 用於暫存 PDF 資料的記憶體快取

# --- API 與應用程式設定 ---
api_key_error_message = ""
try:
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if not app.config['SECRET_KEY'] or not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("錯誤：找不到 SECRET_KEY 或 DATABASE_URL 環境變數。\n")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("錯誤：在 Render 環境變數中找不到 GEMINI_API_KEY。\n")
    
    sendgrid_api_key = os.environ.get("SENDGRID_API_KEY")
    if not sendgrid_api_key:
        raise ValueError("錯誤：在 Render 環境變數中找不到 SENDGRID_API_KEY。\n")

    # Add API_KEY for external API access
    EXTERNAL_API_KEY = os.environ.get("EXTERNAL_API_KEY")
    if not EXTERNAL_API_KEY:
        raise ValueError("錯誤：在 Render 環境變數中找不到 EXTERNAL_API_KEY。\n")

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

class RequestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    endpoint = db.Column(db.String(255), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    response_status = db.Column(db.String(20), nullable=False) # 'success', 'client_error', 'server_error'

    def __repr__(self):
        return f"<RequestLog {self.id} {self.timestamp} {self.endpoint} {self.status_code}>"

class ExternalApiLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)
    api_name = db.Column(db.String(50), nullable=False) # e.g., 'Gemini', 'SendGrid'
    endpoint = db.Column(db.String(255), nullable=True) # The specific API endpoint called
    method = db.Column(db.String(10), nullable=True) # HTTP method (GET, POST)
    request_payload = db.Column(db.Text, nullable=True) # JSON or other payload sent
    response_status_code = db.Column(db.Integer, nullable=True)
    response_content = db.Column(db.Text, nullable=True) # Raw response content
    duration_ms = db.Column(db.Float, nullable=True) # Request duration in milliseconds
    success = db.Column(db.Boolean, nullable=False)
    error_message = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f"<ExternalApiLog {self.id} {self.timestamp} {self.api_name} {self.success}>"

class IChingHexagram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10), unique=True, nullable=False) # e.g., "乾"
    full_name = db.Column(db.String(20), nullable=True) # e.g., "乾為天"
    number = db.Column(db.String(2), unique=True, nullable=False) # e.g., "01"
    symbol = db.Column(db.String(5), nullable=True) # e.g., "䷀"
    hexagram_text = db.Column(db.Text, nullable=True) # 卦辭
    tuan_zhuan = db.Column(db.Text, nullable=True) # 彖傳
    xiang_zhuan_da = db.Column(db.Text, nullable=True) # 大象
    wen_yan = db.Column(db.Text, nullable=True) # 文言傳 (only for Qian/Kun)

    lines = db.relationship('IChingLine', backref='hexagram', lazy=True)

    def __repr__(self):
        return f"<IChingHexagram {self.number}. {self.name}>"

class IChingLine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hexagram_id = db.Column(db.Integer, db.ForeignKey('i_ching_hexagram.id'), nullable=False)
    line_number = db.Column(db.Integer, nullable=False) # 1 to 6, or 7 for 用九
    line_name = db.Column(db.String(10), nullable=False) # e.g., "初九", "九二", "用九"
    line_text = db.Column(db.Text, nullable=True) # 爻辭
    xiang_zhuan_xiao = db.Column(db.Text, nullable=True) # 小象 for this line

    __table_args__ = (db.UniqueConstraint('hexagram_id', 'line_number', name='_hexagram_line_uc'),)

    def __repr__(self):
        return f"<IChingLine {self.hexagram.name} {self.line_name}>"

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

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key_header = request.headers.get('X-API-KEY')
        api_key_param = request.args.get('api_key')

        if not EXTERNAL_API_KEY:
            return jsonify({"error": "API Key 未設定"}), 500

        if api_key_header == EXTERNAL_API_KEY or api_key_param == EXTERNAL_API_KEY:
            return f(*args, **kwargs)
    return decorated_function

def log_request(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = datetime.datetime.now()
        response = f(*args, **kwargs) # Execute the original route function

        # Determine status code and response status
        status_code = 500 # Default to 500 if not explicitly set
        response_status = 'server_error'

        if isinstance(response, tuple): # If the view returns (response, status_code)
            status_code = response[1]
            if 200 <= status_code < 300:
                response_status = 'success'
            elif 400 <= status_code < 500:
                response_status = 'client_error'
            else:
                response_status = 'server_error'
        elif isinstance(response, Response): # If the view returns a Response object
            status_code = response.status_code
            if 200 <= status_code < 300:
                response_status = 'success'
            elif 400 <= status_code < 500:
                response_status = 'client_error'
            else:
                response_status = 'server_error'
        # If response is just a string (e.g., "Hello World"), assume 200 OK
        else:
            status_code = 200
            response_status = 'success'

        user_id = session.get('user_id')

        log_entry = RequestLog(
            timestamp=start_time,
            endpoint=request.path,
            method=request.method,
            status_code=status_code,
            user_id=user_id,
            response_status=response_status
        )
        db.session.add(log_entry)
        db.session.commit()

        return response
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

def generate_relationship_prompt(question: str, hex_data: Dict, moving_line_index: int) -> str:
    # Extract relevant data from hex_data
    main_hex = hex_data.get("本卦", {})
    mutual_hex = hex_data.get("互卦", {})
    changing_hex = hex_data.get("變卦", {})

    # Placeholder for detailed logic to determine upper/lower trigrams,
    # male/female hexagrams, Qian-Kun six sons, etc.
    # This will require more detailed hexagram data than currently available in hex_data
    # For now, I'll use placeholders and focus on the prompt structure.

    # Example: Determine if it's a "Jiao" (交) or "Bu Jiao" (不交) situation
    # This would require mapping hexagrams to their trigram compositions and then to male/female attributes.
    # For simplicity, let's assume we can derive this from hex_data if it were more detailed.
    # For now, I'll use generic descriptions.

    prompt = f'''
請扮演一位精通《周易》卜筮與「乾坤六子」男女取象法的易學專家，擅長以卦名卦義、卦象與爻辭結合現代語言分析感情關係。
你了解婚合之象的原理「交易為吉」——即男下女上為婚合，男上女下為不交。
你也能根據乾坤六子判斷男女性格、婚姻潛質與吉凶。
若為同性婚姻，請依相對陽陰性與角色配對，或用「長下少上」的同性交易原理輔助判斷。

解卦時請遵循以下分析步驟，條理清晰地分段說明。

🔹【一、卦名卦義與經文】

說明此卦的名稱與典故。
本卦：《{main_hex.get('name', '未知')}》
卦辭：{main_hex.get('judgement', '')}

若卦名或卦辭直接提及婚姻（如「女歸吉」、「勿用取女」、「歸妹」），直接給出結論（可成或不可成）。
若卦義模糊，則轉入卦象層面進一步分析。

🔹【二、卦象分析】

說明上卦與下卦屬性（如：上為天、下為地）。
上卦：{main_hex.get('upper_trigram_name', '未知')} (屬性: {main_hex.get('upper_trigram_attribute', '未知')})
下卦：{main_hex.get('lower_trigram_name', '未知')} (屬性: {main_hex.get('lower_trigram_attribute', '未知')})

判斷是否為「交易之象」：
男卦在下、女卦在上 → 男女有交、感情可成。
男卦在上、女卦在下 → 不交、不宜婚。
（此處需根據卦象具體判斷，目前為通用說明）

指出上、下卦屬哪一類乾坤六子：
男卦：乾（父）、震（長男）、坎（中男）、艮（少男）
女卦：坤（母）、巽（長女）、離（中女）、兌（少女）
（此處需根據卦象具體判斷，目前為通用說明）

根據配對關係說明：
長男配長女 → 穩定、門當戶對。
中男配中女 → 情深但多憂慮、坎陷之象。
少男配少女 → 年輕氣盛、情感衝動但變數大。
（此處需根據卦象具體判斷，目前為通用說明）

若有交而卦義不吉（如困、未濟、渙），請說明可能的婚後困境（如多勞、分離、憂慮）。

🔹【三、爻義與爻象分析】

若有變爻，請指出變爻位置與陰陽變化。
動爻：第 {moving_line_index} 爻
（此處需根據爻辭具體分析）

分析「應」與「比」：
遠應（初與四、二與五、三與上）陰陽相應則有情通。
比應（陽上陰下）則為情投意合。
若陰陽不應、上下失交，代表感情不順或緣淺。
（此處需根據爻象具體分析）

若變卦形成交象（男下女上），則為後期可成；反之則可能破局。
變卦：《{changing_hex.get('name', '未知')}》
卦辭：{changing_hex.get('judgement', '')}

🔹【四、同性婚姻輔助原則（如適用）】
（此處需根據具體情況判斷，目前為通用說明）

🔹【五、綜合判斷】

統整卦名、卦象、爻象、變卦後給出整體評價：
（此處需根據綜合分析給出具體評價）

給出建議（例如：「宜順其自然」、「需誠信相待」、「暫緩婚事」、「分則兩利」等）。

🔹【六、附註】

若卦象與爻象相衝，請以變爻或變卦為主。
若卦象雖交而卦義不吉，則為「有情難成」之象。
若無變爻，則以本卦為主。
'''
    return prompt

def generate_marriage_prompt(question: str, main_analysis: Dict, changed_analysis: Dict, interpretation_details: Dict, day_info_str: str) -> str:
    # Extract relevant data from main_analysis, changed_analysis, interpretation_details
    # This will require careful mapping of liuyao_system's output to the prompt's requirements.

    # Placeholder for 世爻, 應爻, 財爻, 官鬼, 子孫, 父母, etc.
    # liuyao_system.py's analysis_result['lines'] contains some of this.
    # We need to iterate through lines to find 世爻, 應爻, 財爻, 官鬼.

    shi_line_info = ""
    ying_line_info = ""
    cai_yao_info = ""
    guan_gui_info = ""
    zi_sun_info = ""
    fu_mu_info = ""

    for line in main_analysis.get('lines', []):
        if line.get('shi_ying') == '世':
            shi_line_info = f"{line.get('position')} {line.get('relative')} {line.get('branch')} ({line.get('element')})"
        elif line.get('shi_ying') == '應':
            ying_line_info = f"{line.get('position')} {line.get('relative')} {line.get('branch')} ({line.get('element')})"
        if line.get('relative') == '妻財':
            cai_yao_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "
        elif line.get('relative') == '官鬼':
            guan_gui_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "
        elif line.get('relative') == '子孫':
            zi_sun_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "
        elif line.get('relative') == '父母':
            fu_mu_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "

    cai_yao_info = cai_yao_info.strip(', ') if cai_yao_info else "未見"
    guan_gui_info = guan_gui_info.strip(', ') if guan_gui_info else "未見"
    zi_sun_info = zi_sun_info.strip(', ') if zi_sun_info else "未見"
    fu_mu_info = fu_mu_info.strip(', ') if fu_mu_info else "未見"

    # Determine upper/lower trigram names and elements
    upper_trigram_name = liuyao.HEXAGRAM_COMPOSITION.get(main_analysis['hex_name'], ('', ''))[0]
    lower_trigram_name = liuyao.HEXAGRAM_COMPOSITION.get(main_analysis['hex_name'], ('', ''))[1]
    upper_trigram_element = liuyao.PALACE_ELEMENTS.get(upper_trigram_name, '未知')
    lower_trigram_element = liuyao.PALACE_ELEMENTS.get(lower_trigram_name, '未知')

    # Determine 世爻為陽/陰, 應爻為陽/陰
    shi_yao_yin_yang = ""
    ying_yao_yin_yang = ""
    for line in main_analysis.get('lines', []):
        if line.get('shi_ying') == '世':
            shi_yao_yin_yang = "陽" if line.get('yin_yang') == 1 else "陰"
        elif line.get('shi_ying') == '應':
            ying_yao_yin_yang = "陽" if line.get('yin_yang') == 1 else "陰"

    # Determine if it's a "Jiao" (交易之象) or "Bu Jiao" (不交)
    # This is complex and requires mapping trigrams to male/female attributes.
    # For now, I'll provide the trigram names and let Gemini infer.
    jiao_xiang = "（需AI判斷）" # Placeholder

    prompt = f'''
你是一位精通《易經》、《增刪卜易》與《焦氏易林》的卜卦專家，熟悉六爻婚姻章七首中各條象理、陰陽配偶論、財鬼生剋、世應比和之法。
請根據我提供的卦象資料，進行婚姻占卜白話解釋，並從下列七個面向全面說明：

**占卜問題：** {question}
**起卦日期資訊：** {day_info_str}

**卦象資料：**
本卦：《{main_analysis.get('hex_name', '未知')}》
變卦：《{changed_analysis.get('hex_name', '未知') if changed_analysis else '無變卦'}》
動爻：第 {main_analysis.get('moving_lines_in_main', ['無'])[0]} 爻 (若有)

**本卦爻象細節：**
{liuyao.format_for_llm(main_analysis, changed_analysis, interpretation_details, day_info_str, question)}

**關鍵爻資訊：**
世爻：{shi_line_info} ({shi_yao_yin_yang})
應爻：{ying_line_info} ({ying_yao_yin_yang})
財爻 (妻)：{cai_yao_info}
官鬼 (夫)：{guan_gui_info}
子孫 (情緣)：{zi_sun_info}
父母 (家庭支持)：{fu_mu_info}

---

🧭 **一、卦象結構與關鍵爻**

說明卦名、內外卦五行、世應位置，指出「財爻（妻）」、「官鬼（夫）」的狀態。

💍 **二、婚姻吉凶判斷**

依〈婚姻章〉口訣對照說明：
「內身陽鬼丈夫持」
「外應財陰總是妻」
「世應相生婚大吉」
「比和世應配相宜」
等句，用白話指出婚姻能否順利、彼此是否相生相剋。

👫 **三、男女配合與感情互動**

根據詩句：
「青龍六合扶為美，三合子孫臨更奇，應動三刑刑莫問，外交六害害無疑。」
分析夫妻是否和諧、有無貴人撮合、或有刑沖害之象。

💞 **四、感情緣份深淺**

引用歌訣：
「一奇一耦成親順，雙鬼雙財匹配違。」
說明雙方陰陽是否相合，是否有外緣或再婚之象。

👨‍👩‍👧 **五、性格與外貌分析**

依下列詩句進行白話解釋：
「坎主心聰艮沉靜，兌必和柔巽必恭，坤爻寬厚乾剛正，文明女子為逢離，智慧男兒因見震。」
「乾宮面部大而寬，坤主魁肥莫小看，艮卦決然身體小，坎爻定是臉團圓。」
逐條對應男女的外型與性格特徵。

🏠 **六、家庭與長久性**

引用詩句：
「若逢天寡天鰥殺，夫婦應知不久長。」
「陰陽得位俱稱吉，純陰枉使心和力，純陽退悔不成婚。」
分析婚後是否長久、是否有孤寡、爭執或再婚之兆。

💰 **七、財福與生活條件**

依歌訣：
「青龍旺相臨財位，娶妻萬倍有資粧。」
「本宮無炁財有炁，婦舍雖貧女容媚；本宮旺相財囚死，婦舍雖貧女不美。」
以白話分析婚後財運、配偶條件、生活福分。

✍️ **最後結語（卜辭）**

請用一段古風收尾總斷，總結婚姻結果（如「此卦陰陽相生，情投意合，可成良緣」或「陰陽乖隔，緣薄如霧，不宜勉強」）。

✅ **補充規則**

若世爻為陽、應爻為陰 → 男占女
若世爻為陰、應爻為陽 → 女占男

財爻代表妻、官鬼代表夫、子孫代表情緣、父母代表媒人與家庭支持

動爻變化則參考變卦吉凶，重點觀「財鬼生剋」與「世應關係」

📘 **範例開場句（可附卦）**

問婚姻卦：{main_analysis.get('hex_name', '未知')} ({upper_trigram_name}上{lower_trigram_name}下)，世爻持{shi_line_info}，應爻臨{ying_line_info}。
'''
    return prompt

def generate_career_prompt(question: str, main_analysis: Dict, changed_analysis: Dict, interpretation_details: Dict, day_info_str: str, yilin_verse: Dict = None) -> str:
    # Extract relevant data from main_analysis, changed_analysis, interpretation_details
    # This will require careful mapping of liuyao_system's output to the prompt's requirements.

    # Placeholder for 世爻, 應爻, 官鬼, 父母爻, 子孫, 兄弟, 妻財.
    shi_line_info = ""
    ying_line_info = ""
    guan_gui_info = ""
    fu_mu_info = ""
    zi_sun_info = ""
    xiong_di_info = ""
    cai_yao_info = ""

    for line in main_analysis.get('lines', []):
        if line.get('shi_ying') == '世':
            shi_line_info = f"{line.get('position')} {line.get('relative')} {line.get('branch')} ({line.get('element')})"
        elif line.get('shi_ying') == '應':
            ying_line_info = f"{line.get('position')} {line.get('relative')} {line.get('branch')} ({line.get('element')})"
        if line.get('relative') == '官鬼':
            guan_gui_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "
        elif line.get('relative') == '父母':
            fu_mu_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "
        elif line.get('relative') == '子孫':
            zi_sun_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "
        elif line.get('relative') == '兄弟':
            xiong_di_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "
        elif line.get('relative') == '妻財':
            cai_yao_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "

    guan_gui_info = guan_gui_info.strip(', ') if guan_gui_info else "未見"
    fu_mu_info = fu_mu_info.strip(', ') if fu_mu_info else "未見"
    zi_sun_info = zi_sun_info.strip(', ') if zi_sun_info else "未見"
    xiong_di_info = xiong_di_info.strip(', ') if xiong_di_info else "未見"
    cai_yao_info = cai_yao_info.strip(', ') if cai_yao_info else "未見"

    # Yilin verse
    yilin_text = "無焦氏易林詩句"
    if yilin_verse:
        yilin_text = f"本卦《{yilin_verse['from']}》變《{yilin_verse['to']}》：{yilin_verse['verse']}"

    prompt = f'''
你是一位精通《易經》、《增刪卜易》與《焦氏易林》的卜卦專家，熟悉六爻婚姻章七首中各條象理、陰陽配偶論、財鬼生剋、世應比和之法。
請依據我輸入的卦象資料（含本卦、互卦、變卦、焦氏易林詩句、占卜主題），
生成一份完整、白話、結構清晰的「仕宦卦解析報告」，格式如下：

**占卜問題：** {question}
**起卦日期資訊：** {day_info_str}

**卦象資料：**
本卦：《{main_analysis.get('hex_name', '未知')}》
變卦：《{changed_analysis.get('hex_name', '未知') if changed_analysis else '無變卦'}》
動爻：第 {main_analysis.get('moving_lines_in_main', ['無'])[0]} 爻 (若有)

**本卦爻象細節：**
{liuyao.format_for_llm(main_analysis, changed_analysis, interpretation_details, day_info_str, question)}

**關鍵爻資訊：**
世爻：{shi_line_info}
應爻：{ying_line_info}
官鬼 (職位/丈夫)：{guan_gui_info}
父母爻 (文書/批示)：{fu_mu_info}
子孫 (情緣/下屬)：{zi_sun_info}
兄弟 (競爭者/同僚)：{xiong_di_info}
妻財 (財物/妻子)：{cai_yao_info}

---

一、卦象總覽

本卦名稱與象義：說明卦德與官運象徵（例如「明夷卦：內明外暗，宜守位以避禍」）。

變卦與互卦意義：指出事勢的潛在變化與發展方向。

焦氏易林詩句：完整引用詩文，逐句解釋其官祿象徵。
{yilin_text}

二、仕宦章理論分析（六親＋納甲＋官象）
1️⃣ 世應定位

世爻：代表我方／本人仕途地位。
應爻：代表外界（長官、組織、人事單位）。
說明二者相生相剋之關係，推判人際、升遷、或外部壓力。

2️⃣ 官鬼與父母爻

官鬼旺相：代表官運上升、職權增加。
父母爻動：代表文書批示、公文、考核等機會。
若父母爻旺而相生，為得上命之象；若剋身則主責難或審核壓力。

3️⃣ 驛馬、符印、太歲

驛馬動：主調職、陞遷、外派、新任命。
符印臨官鬼或世爻：主得詔命、得上賞、功名成。
太歲合世：主入朝見上級、升遷得遇貴人。

4️⃣ 子孫、兄弟、財爻

子孫持世：主心逸志散、易招懶惰，求官不成。
兄弟旺動：主競爭者多，或同僚牽制。
妻財動剋官鬼：主財物耗損、爭權導致官運受阻。

三、《仕宦章》白話判斷依據

請根據以下古訣逐條比對、轉譯成現代語境：

「父動為先鬼次看」 → 若父爻動且生世，則先得上命或考績提拔。
「驛馬相扶官職遷」 → 若驛馬臨官鬼或世爻，主有陞遷、外調、調任新職。
「鬼臨身世得官真」 → 官鬼旺相且臨身，是真得職之象。
「子孫持世必隳官」 → 若子爻主世，宜守不宜動。
「太歲合時見天子」 → 若太歲與世爻相合，主有機會見上級、受任命。
「人吏空亡難立腳」 → 若初爻或人吏位空亡，主組織內下屬不力或執行困難。
「符印動時喜詔書」 → 若父母或官爻兼符印動，主文書命令將至。
「身剋人吏百憂攢」 → 若世剋初爻，主壓力過重、人事緊張。

四、焦氏易林詩義解釋

將焦氏詩文逐句白話解釋，結合官運意象：

比如：「稷為堯使」象徵賢臣受命、有才能被重用；
「拜請百福」象徵得上司支持、職位安穩；
「賜我喜子」象徵部屬得力、計畫圓滿完成。

五、現代語境解讀（仕途應用）

結合卦象與詩意，判斷目前職場情況（如內部問題、升遷機會、人事派系）。
提出具體行動建議：
若「宜靜」則建議守勢、等待機會。
若「宜動」則主積極請命、外調可成。
若「應剋世」則防上級壓力與同僚爭功。

六、吉凶總評

綜合整體卦象與仕宦章判法，歸納出：
官運總評（上升／停滯／下滑）
貴人與障礙來源
近期吉時（可依月令、太歲）
建議採取之具體行動（如「宜陳功報上」、「暫避鋒芒」、「請調外任」等）
'''
    return prompt

def generate_illness_prompt(question: str, main_analysis: Dict, changed_analysis: Dict, interpretation_details: Dict, day_info_str: str, yilin_verse: Dict = None, inquirer_relationship: str = "") -> str:
    # Extract relevant data from main_analysis, changed_analysis, interpretation_details
    # This will require careful mapping of liuyao_system's output to the prompt's requirements.

    # Placeholder for 世爻, 應爻, 官鬼, 父母爻, 子孫, 兄弟, 妻財.
    shi_line_info = ""
    ying_line_info = ""
    guan_gui_info = ""
    fu_mu_info = ""
    zi_sun_info = ""
    xiong_di_info = ""
    cai_yao_info = ""

    for line in main_analysis.get('lines', []):
        if line.get('shi_ying') == '世':
            shi_line_info = f"{line.get('position')} {line.get('relative')} {line.get('branch')} ({line.get('element')})"
        elif line.get('shi_ying') == '應':
            ying_line_info = f"{line.get('position')} {line.get('relative')} {line.get('branch')} ({line.get('element')})"
        if line.get('relative') == '官鬼':
            guan_gui_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "
        elif line.get('relative') == '父母':
            fu_mu_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "
        elif line.get('relative') == '子孫':
            zi_sun_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "
        elif line.get('relative') == '兄弟':
            xiong_di_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "
        elif line.get('relative') == '妻財':
            cai_yao_info += f"{line.get('position')} {line.get('branch')} ({line.get('element')}), "

    guan_gui_info = guan_gui_info.strip(', ') if guan_gui_info else "未見"
    fu_mu_info = fu_mu_info.strip(', ') if fu_mu_info else "未見"
    zi_sun_info = zi_sun_info.strip(', ') if zi_sun_info else "未見"
    xiong_di_info = xiong_di_info.strip(', ') if xiong_di_info else "未見"
    cai_yao_info = cai_yao_info.strip(', ') if cai_yao_info else "未見"

    # Yilin verse
    yilin_text = "無焦氏易林詩句"
    if yilin_verse:
        yilin_text = f"本卦《{yilin_verse['from']}》變《{yilin_verse['to']}》：{yilin_verse['verse']}"

    prompt = f'''
你是一位精通《周易》六爻、焦氏易林與京房納甲法的易學大師，
熟悉《疾病章》古法判病之理，能以白話方式說明卦中疾病輕重、臟腑歸屬、康復時機、死生關口、親屬關聯。

請依據我輸入的卦象資料（含本卦、變卦、互卦、焦氏易林詩句、占卜主題與代問者關係），
生成一份完整、現代化、條理分明的疾病卦分析報告，格式如下：

**占卜問題：** {question}
**代問者關係：** {inquirer_relationship if inquirer_relationship else '本人占卜'}
**起卦日期資訊：** {day_info_str}

**卦象資料：**
本卦：《{main_analysis.get('hex_name', '未知')}》
變卦：《{changed_analysis.get('hex_name', '未知') if changed_analysis else '無變卦'}》
動爻：第 {main_analysis.get('moving_lines_in_main', ['無'])[0]} 爻 (若有)

**本卦爻象細節：**
{liuyao.format_for_llm(main_analysis, changed_analysis, interpretation_details, day_info_str, question)}

**關鍵爻資訊：**
世爻：{shi_line_info}
應爻：{ying_line_info}
官鬼 (病根/病邪)：{guan_gui_info}
父母爻 (氣血/精神/藥效)：{fu_mu_info}
子孫爻 (藥/醫治/免疫力)：{zi_sun_info}
兄弟爻 (氣脈阻礙/血氣失調)：{xiong_di_info}
妻財爻 (飲食/身體負擔)：{cai_yao_info}

---

一、卦象總覽

本卦名稱與象義：說明卦德與病情整體氣象（如「明夷卦：暗中受損，主氣血不暢」）。

變卦與互卦提示：指出病勢轉變方向或康復關鍵。

焦氏易林詩句：引用並白話解釋其中健康象徵。
{yilin_text}

二、六親定位與問卜關係

說明問卜者與病者關係（本人、父母、配偶、子女、朋友、下屬）。
（此處需AI根據 inquirer_relationship 判斷）

說明代表病者的爻（通常取「世爻」或「被問之爻」）。
（此處需AI根據 inquirer_relationship 判斷）

分析六親的關聯：

父母爻：主氣血、精神、文書與藥效。
妻財爻：主飲食、身體負擔與耗損。
官鬼爻：為病根、病邪、外來侵擾。
子孫爻：為藥、醫治、免疫力、康復象。
兄弟爻：為氣脈阻礙、血氣失調、外力干擾。

三、《疾病章》理論逐條白話分析
1️⃣ 病源與輕重

官鬼為病根：鬼動則病重；鬼靜則病緩。
子孫生世：主藥效顯、病可癒。
子孫化鬼：主藥反為害。
官鬼化兄／化財：主病轉壞、財耗多。
官鬼化子：主轉安、病漸癒。
六爻靜卦：主病久難癒。
官鬼旺相、財旺身空：主危險、有生死之兆。

2️⃣ 病象與臟腑歸屬

請根據五行與方位分析病位：
水為腰腎、泌尿、生殖系統
金為肺與氣管
火為心臟與血脈
木為肝膽與筋骨
土為脾胃與腫脹

並依八卦身體對應說明：
乾：頭、上焦、精神
坤：腹、腸胃
震：足
巽：手
坎：耳、腎
離：目、心
艮：鼻
兌：口

例：
「水鬼臨身」 → 主腎水不足、泌尿系統問題。
「火鬼貼身」 → 主發炎、高燒、心血不寧。

3️⃣ 特殊神煞應驗

勾陳臨身：病阻難解，或有外傷。
玄武臨命：主暗疾、感染、拖延。
螣蛇白虎動：主驚恐、手術、喪厄。
身命空亡：主虛脫、危象、魂不附體。
青龍子孫旺：主良醫得遇、藥效顯著。

4️⃣ 卦例對照（古法直譯）

以下古句轉為白話提示：

「逢龍見子放心寬」 → 子孫旺、青龍扶，主有康復希望。
「官鬼臨身更不堪」 → 病邪入體，難以控制。
「財旺身空身必喪」 → 體虛而勞、耗財又損命。
「鬼化為財凶有準」 → 病拖財散，恐有後續惡化。
「鬼爻化子瘥無疑」 → 若病鬼化子孫，主得藥效痊癒。
「虎鬼同興應哭泣」 → 白虎與鬼同動，主凶兆。
「龍孫並旺保平安」 → 青龍子孫動旺，主康復。
「六爻安靜尤難瘥」 → 若無一爻動，主久病難起。
「明夷蠱夬剝豐同」 → 凡得此六卦，多主病危或臟腑衰。

四、家屬代問應象解讀

根據代問者不同，說明卦義如何轉換：
子問父母 → 父母爻為主。
父母問子女 → 子孫爻為主。
妻問夫 → 官鬼爻為主。
夫問妻 → 財爻為主。
兄弟問兄弟 → 兄爻為主。

五、現代語境解析

以白話說明病勢走向與行動建議：
若「子孫旺」→ 可治、宜信醫。
若「官鬼旺」→ 病根深、宜守不宜動。
若「財動剋世」→ 體力虛、不可勞累。
若「父母旺」→ 有藥可解。
若「白虎動」→ 應防手術或喪厄。

六、吉凶總評

病勢趨向：漸安／拖延／危險／轉機出現。
康復時機：指出依卦氣五行推測的月份或節氣。
行動建議：靜養、換醫、調理、忌勞、或宜轉信念。
'''
    return prompt

def call_gemini_api(prompt: str) -> str:
    start_time = datetime.datetime.now()
    success = False
    error_message = None
    response_text = ""
    status_code = None

    try:
        model = genai.GenerativeModel('models/gemini-pro-latest')
        response = model.generate_content(prompt)
        response_text = response.text
        status_code = 200 # Assuming 200 for successful content generation
        success = True
        md = MarkdownIt()
        html = md.render(response_text)
        return Markup(html)
    except Exception as e:
        error_message = str(e)
        response_text = f"<p>呼叫 Gemini API 時出錯：</p><p>{e}</p>"
        status_code = 500 # Assuming 500 for API call failure
        return Markup(response_text)
    finally:
        end_time = datetime.datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        log_entry = ExternalApiLog(
            timestamp=start_time,
            api_name='Gemini',
            endpoint='/models/gemini-pro-latest', # Generic endpoint for Gemini
            method='POST', # Assuming it's a POST request
            request_payload=prompt,
            response_status_code=status_code,
            response_content=response_text,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        db.session.add(log_entry)
        db.session.commit()

def send_divination_email(question, numbers, hex_data, interpretation_html, user):
    start_time = datetime.datetime.now()
    success = False
    error_message = None
    response_status_code = None
    response_content = None

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
        response_status_code = response.status_code
        response_content = response.body # SendGrid response body
        if not (response.status_code >= 200 and response.status_code < 300):
            flash(f'郵件發送失敗，錯誤碼：{response.status_code}', 'error')
            error_message = f'SendGrid 錯誤碼: {response.status_code}'
        else:
            success = True
    except Exception as e:
        print(f"Email sending failed: {e}")
        flash(f'郵件發送時發生錯誤: {e}', 'error')
        error_message = str(e)
    finally:
        end_time = datetime.datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        log_entry = ExternalApiLog(
            timestamp=start_time,
            api_name='SendGrid',
            endpoint='/mail/send', # SendGrid's mail send endpoint
            method='POST',
            request_payload=f"Subject: {subject}, To: is33.wu@gmail.com", # Log relevant parts of the request
            response_status_code=response_status_code,
            response_content=response_content,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        db.session.add(log_entry)
        db.session.commit()

def send_liuyao_email(question, input_date, day_info_str, main_analysis, changed_analysis, moving_lines, interpretation_details, gemini_interpretation, user):
    start_time = datetime.datetime.now()
    success = False
    error_message = None
    response_status_code = None
    response_content = None

    try:
        subject = f"六爻納甲占卜結果：{question[:20]}..."
        
        # Build the HTML content for the email
        body_html = f'''
        <html>
        <body style="font-family: sans-serif;">
            <h2>占卜問題：</h2>
            <p>{question}</p>
            <hr>
            <h2>起卦資訊：</h2>
            <ul>
                <li><b>占卜會員：</b> {user['username']}</li>
                <li><b>占卜日期：</b> {input_date if input_date else "今天"}</li>
                <li><b>日期資訊：</b> {day_info_str}</li>
                <li><b>本卦：</b> {main_analysis['hex_name']}</li>
                {'<li><b>變卦：</b> ' + changed_analysis['hex_name'] + '</li>' if changed_analysis else ''}
            </ul>
            <hr>
            <h2>本卦分析: {main_analysis['hex_name']}</h2>
            <p><strong>卦名:</strong> {main_analysis['hex_name']} ({main_analysis['palace_name']}宮{main_analysis['gen_name']})</p>
            <p><strong>五行屬性:</strong> {main_analysis['palace_element']}</p>
            <h3>爻象細節:</h3>
            <pre style="background-color: #e9ecef; padding: 1rem; border-radius: 5px;">
        '''
        
        # Add hexagram lines to the email body
        for i, line in enumerate(reversed(main_analysis["lines"])):
            line_num = 6 - i
            moving_marker = "●" if line_num in moving_lines else ""
            empty_marker = "空" if line['is_empty'] else ""
            fu_shen_str = f"伏({line['fu_shen']['relative']}{line['fu_shen']['branch']})" if line['fu_shen'] else ""
            full_stem_branch = f"{line['stem']}{line['branch']}"
            yin_yang_symbol = "—" if line['yin_yang'] == 1 else "--"
            
            line_details_str = ""
            if interpretation_details['line_details'].get(line_num):
                line_details_str = f" ({', '.join(interpretation_details['line_details'][line_num])})"

            body_html += f'''{line['position']:<4}{fu_shen_str:<8}{line['shi_ying']:<3}{yin_yang_symbol:<3}{moving_marker:<2}{empty_marker:<3}{line['six_god']:<4}{full_stem_branch:<6}{line['branch']:<4}{line['element']:<4}{line['relative']:<5}{line_details_str}\n'''
        body_html += '</pre>'

        if changed_analysis:
            body_html += f'''
            <hr>
            <h2>變卦分析: {changed_analysis['hex_name']}</h2>
            <h3>動爻變化:</h3>
            <ul>
            '''
            for line_num in moving_lines:
                original_line = main_analysis["lines"][line_num - 1]
                changed_line = changed_analysis["lines"][line_num - 1]
                body_html += f'''<li>{original_line['position']} {original_line['relative']} {original_line['branch']} → {changed_line['relative']} {changed_line['branch']}</li>\n'''
            body_html += '</ul>'

        body_html += f'''
            <hr>
            <h2>斷卦參考</h2>
            '''
        if interpretation_details['special_type']:
            body_html += f'''<p><strong>特殊卦象:</strong> {interpretation_details['special_type']}</p>'''
        else:
            body_html += f'''<p>無特殊卦象。</p>'''

        body_html += f'''
            <hr>
            <h2>AI 綜合解讀：</h2>
            {gemini_interpretation}
        </body>
        </html>
        '''
        
        message = Mail(
            from_email='is33.wu@gmail.com', # Sender email
            to_emails='is33.wu@gmail.com', # Recipient email
            subject=subject,
            html_content=body_html
        )
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        response_status_code = response.status_code
        response_content = response.body # SendGrid response body
        if not (response.status_code >= 200 and response.status_code < 300):
            flash(f'六爻郵件發送失敗，錯誤碼：{response.status_code}', 'error')
            error_message = f'SendGrid 錯誤碼: {response.status_code}'
        else:
            success = True
    except Exception as e:
        print(f"Liu Yao Email sending failed: {e}")
        flash(f'六爻郵件發送時發生錯誤: {e}', 'error')
        error_message = str(e)
    finally:
        end_time = datetime.datetime.now()
        duration_ms = (end_time - start_time).total_seconds() * 1000
        log_entry = ExternalApiLog(
            timestamp=start_time,
            api_name='SendGrid',
            endpoint='/mail/send', # SendGrid's mail send endpoint
            method='POST',
            request_payload=f"Subject: {subject}, To: is33.wu@gmail.com", # Log relevant parts of the request
            response_status_code=response_status_code,
            response_content=response_content,
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        db.session.add(log_entry)
        db.session.commit()

@app.route("/api/meihua_divine", methods=["POST"])
@api_key_required
@log_request
def api_meihua_divine():
    """
    梅花易數占卜 API 端點。
    接收占卜問題和三組數字，返回占卜結果和 AI 解讀。
    ---
    請求範例 (JSON Body):
    {
        "question": "我的事業發展前景如何？",
        "num1": 123,
        "num2": 456,
        "num3": 789
    }
    --- 
    回應範例 (JSON Response):
    {
        "ai_interpretation_html": "<p>AI 解讀內容...</p>",
        "changing_hexagram": "火天大有",
        "changing_hexagram_judgement": "大有：元亨。",
        "main_hexagram": "乾為天",
        "main_hexagram_judgement": "乾：元亨利貞。",
        "message": "梅花易數占卜成功",
        "moving_line": 6,
        "mutual_hexagram": "天風姤",
        "mutual_hexagram_judgement": "姤：女壯，勿用取女。",
        "numbers": [123, 456, 789],
        "question": "我的事業發展前景如何？",
        "status": "success"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "無效的 JSON 輸入"}), 400

    question = data.get("question")
    num1 = data.get("num1")
    num2 = data.get("num2")
    num3 = data.get("num3")

    if not all([question, num1, num2, num3]):
        return jsonify({"error": "缺少必要的占卜參數 (question, num1, num2, num3)"}), 400
    
    try:
        num1 = int(num1)
        num2 = int(num2)
        num3 = int(num3)
        if not (100 <= num1 <= 999 and 100 <= num2 <= 999 and 100 <= num3 <= 999):
            return jsonify({"error": "數字必須介於 100 到 999 之間"}), 400
    except ValueError:
        return jsonify({"error": "數字格式錯誤，請輸入有效的整數"}), 400

    # 執行梅花易數的計算邏輯
    numbers = (num1, num2, num3)
    lines, moving_line = calculate_hexagram(num1, num2, num3)
    hex_data = meihua.interpret_hexagrams_from_lines(lines, moving_line)

    prompt = generate_interpretation_prompt(question, numbers, hex_data, moving_line)
    interpretation_html = call_gemini_api(prompt)

    if "呼叫 Gemini API 時出錯" in interpretation_html:
        return jsonify({"error": "AI 解讀服務暫時無法使用", "details": str(interpretation_html)}), 500 # 將 Markup 轉換為字串

    # 如果您需要對 API 呼叫也進行次數限制，可以在此處實作
    # user = User.query.get(session['user_id']) # 如果有登入驗證
    # if user and not user.is_admin and user.usage_count >= 3:
    #     return jsonify({"error": "您的占卜次數已達上限"}), 403
    # if user:
    #     user.usage_count += 1
    #     db.session.commit()

    response_data = {
        "question": question,
        "numbers": numbers,
        "main_hexagram": hex_data["本卦"]["name"],
        "main_hexagram_judgement": hex_data["本卦"]["judgement"],
        "mutual_hexagram": hex_data["互卦"]["name"],
        "mutual_hexagram_judgement": hex_data["互卦"]["judgement"],
        "changing_hexagram": hex_data["變卦"]["name"],
        "changing_hexagram_judgement": hex_data["變卦"]["judgement"],
        "moving_line": moving_line,
        "ai_interpretation_html": str(interpretation_html), # 將 Markup 物件轉換為字串
        "status": "success",
        "message": "梅花易數占卜成功"
    }
    return jsonify(response_data), 200

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
        "2035-05-06","2035-05-21","2035-06-06","2035-06-21",
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
        "2044-05-05","2044-05-20","2044-06-05","2044-06-20",
        "2044-07-06","2044-07-22","2044-08-07","2044-08-22",
        "2044-09-07","2044-09-22","2044-10-07","2044-10-23",
        "2044-11-07","2044-11-21","2044-12-06","2044-12-21"
    ], []),
    2045: ([
        "2045-01-05","2045-01-19","2045-02-03","2045-02-18",
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
        results[term_name] = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            
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
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
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

# --- Flask 路由 ---

@app.route("/login", methods=['GET', 'POST'])
@log_request
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
@log_request
def register():
    flash('註冊功能已關閉，請聯絡管理員以取得帳號。', 'info')
    return redirect(url_for('login'))

@app.route("/logout")
@login_required
@log_request
def logout():
    session.clear()
    flash('您已成功登出', 'success')
    return redirect(url_for('login'))

@app.route("/")
@login_required
@log_request
def index():
    if api_key_error_message:
        return f'''<h1>應用程式設定錯誤</h1><p>{api_key_error_message}</p>''', 500
    user = User.query.get(session['user_id'])
    return render_template("index.html", user=user)

@app.route("/meihua")
@login_required
@log_request
def meihua_divine_page():
    user = User.query.get(session['user_id'])
    return render_template("meihua_divine.html", user=user)

@app.route("/create_hexagram", methods=["GET", "POST"])
@login_required
@admin_required # Only admin can create hexagrams
@log_request
def create_hexagram():
    if request.method == "POST":
        name = request.form.get("name")
        full_name = request.form.get("full_name")
        number = request.form.get("number")
        symbol = request.form.get("symbol")
        hexagram_text = request.form.get("hexagram_text")
        tuan_zhuan = request.form.get("tuan_zhuan")
        xiang_zhuan_da = request.form.get("xiang_zhuan_da")
        wen_yan = request.form.get("wen_yan")

        if not name or not number:
            flash("卦名和數字為必填項。", "error")
            return redirect(url_for("create_hexagram"))

        existing_hexagram = IChingHexagram.query.filter_by(name=name).first()
        if existing_hexagram:
            flash(f"卦名 {name} 已存在。", "error")
            return redirect(url_for("create_hexagram"))
        
        existing_number = IChingHexagram.query.filter_by(number=number).first()
        if existing_number:
            flash(f"卦數 {number} 已存在。", "error")
            return redirect(url_for("create_hexagram"))

        hexagram = IChingHexagram(
            name=name,
            full_name=full_name,
            number=number,
            symbol=symbol,
            hexagram_text=hexagram_text,
            tuan_zhuan=tuan_zhuan,
            xiang_zhuan_da=xiang_zhuan_da,
            wen_yan=wen_yan
        )
        db.session.add(hexagram)
        db.session.commit()

        # Process lines
        for i in range(1, 8): # 1 to 7 for lines (including 用九)
            line_name = request.form.get(f"line_{i}_name")
            line_text = request.form.get(f"line_{i}_text")
            xiang_zhuan_xiao = request.form.get(f"line_{i}_xiang_zhuan_xiao")

            if line_name and (line_text or xiang_zhuan_xiao): # Only save if line name and some content exist
                line = IChingLine(
                    hexagram_id=hexagram.id,
                    line_number=i,
                    line_name=line_name,
                    line_text=line_text,
                    xiang_zhuan_xiao=xiang_zhuan_xiao
                )
                db.session.add(line)
        db.session.commit()

        flash(f"卦象 {name} 建立成功！", "success")
        return redirect(url_for("yilin_index")) # Redirect to yilin_index or a hexagram list page

    return render_template("create_hexagram.html")

@app.route("/admin", methods=['GET', 'POST'])
@admin_required
@log_request
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

@app.route("/admin/request_logs")
@admin_required
@log_request
def request_logs():
    logs = RequestLog.query.order_by(RequestLog.timestamp.desc()).all()
    return render_template("request_logs.html", logs=logs)

@app.route("/admin/external_api_logs")
@admin_required
@log_request
def external_api_logs():
    logs = ExternalApiLog.query.order_by(ExternalApiLog.timestamp.desc()).all()
    return render_template("external_api_logs.html", logs=logs)

@app.route("/admin/set_count/<int:user_id>", methods=['POST'])
@admin_required
@log_request
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
@log_request
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
@log_request
def divine():
    user = User.query.get(session['user_id'])
    if not user.is_admin and user.usage_count >= 3:
        flash(f'您的占卜次數已達 3 次上限，無法再使用。', 'error')
        return redirect(url_for('meihua_divine_page'))
    question = request.form.get("question")
    category = request.form.get("category") # Get the category

    try:
        num1 = int(request.form.get("num1"))
        num2 = int(request.form.get("num2"))
        num3 = int(request.form.get("num3"))
        numbers = (num1, num2, num3)
    except (ValueError, TypeError):
        flash("輸入的數字格式錯誤，請返回上一頁修正。", "error")
        return redirect(url_for('meihua_divine_page'))
    lines, moving_line = calculate_hexagram(num1, num2, num3)
    hex_data = meihua.interpret_hexagrams_from_lines(lines, moving_line)

    # Select prompt based on category
    if category == "relationship":
        prompt = generate_relationship_prompt(question, hex_data, moving_line)
    else: # Default to general interpretation
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
            'moving_line': moving_line,
            'interpretation_html': interpretation_html,
            'user': {'username': user.username}
        }
        return redirect(url_for('show_result', result_id=result_id))

@app.route("/result/<result_id>")
@login_required
@log_request
def show_result(result_id):
    result_data = TEMP_RESULTS.get(result_id)
    if not result_data:
        flash('找不到占卜結果或連結已失效。', 'error')
        return redirect(url_for('index'))
    
    return render_template("result.html", 
                           question=result_data['question'], 
                           numbers=result_data['numbers'],
                           hex_data=result_data['hex_data'],
                           moving_line=result_data['moving_line'],
                           interpretation=result_data['interpretation_html'],
                           result_id=result_id)

@app.route("/liuyao", methods=["GET", "POST"])
@login_required
@admin_required
@log_request
def liuyao_divine():
    if request.method == "POST":
        user = User.query.get(session['user_id'])
        # Add usage limit check if desired, similar to meihua
        if not user.is_admin and user.usage_count >= 3:
            flash('您的六爻占卜次數已達上限，無法再使用。', 'error')
            return redirect(url_for('index'))

        input_date_str = request.form.get("input_date")
        lines_str = request.form.get("lines")
        moving_lines_str = request.form.get("moving_lines")
        question = request.form.get("question")
        category = request.form.get("category") # Get the category

        input_date = None
        if input_date_str:
            try:
                input_date = datetime.datetime.strptime(input_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("日期格式錯誤，請使用 YYYY-MM-DD 格式。", "error")
                return redirect(url_for('liuyao_divine'))

        try:
            lines = tuple(int(x.strip()) for x in lines_str.split(','))
            if len(lines) != 6 or not all(x in (0, 1) for x in lines):
                flash("六爻輸入格式錯誤，請輸入六個0或1，用逗號分隔。", "error")
                return redirect(url_for('liuyao_divine'))
        except ValueError:
            flash("六爻輸入格式錯誤，請輸入數字。", "error")
            return redirect(url_for('liuyao_divine'))

        moving_lines = []
        if moving_lines_str:
            try:
                moving_lines = [int(x.strip()) for x in moving_lines_str.split(',') if x.strip().isdigit() and 1 <= int(x.strip()) <= 6]
            except ValueError:
                flash("動爻輸入格式錯誤，請輸入1到6的數字，用逗號分隔。", "error")
                return redirect(url_for('liuyao_divine'))

        # Call liuyao_system functions
        day_stem, day_branch, day_element, month_branch = liuyao.get_day_info(input_date)
        empty_branches = liuyao.get_kong_wang(day_stem, day_branch)

        hex_name = liuyao.get_hexagram_from_lines(lines)
        if hex_name == "未知卦":
            flash(f"錯誤：輸入的爻象 {lines} 無法對應到任何已知卦象。", "error")
            return redirect(url_for('liuyao_divine'))

        main_analysis, error = liuyao.analyze_hexagram(hex_name, day_stem, day_branch, day_element)
        if error:
            flash(f"卦象分析錯誤: {error}", "error")
            return redirect(url_for('liuyao_divine'))

        # Add gen_name to main_analysis
        gen_name_list = [gn for p, h_list in liuyao.PALACE_DATA.items() if main_analysis['hex_name'] in h_list for gn in liuyao.GENERATION_NAMES if h_list.index(main_analysis['hex_name']) == liuyao.GENERATION_NAMES.index(gn)]
        main_analysis['gen_name'] = gen_name_list[0] if gen_name_list else '未知'

        changed_analysis = None
        if moving_lines:
            changed_hex_name = liuyao.get_changed_hexagram_name(hex_name, moving_lines)
            if changed_hex_name != "未知卦":
                changed_analysis, _ = liuyao.analyze_hexagram(changed_hex_name, day_stem, day_branch, day_element)
                # Add gen_name to changed_analysis
                gen_name_list = [gn for p, h_list in liuyao.PALACE_DATA.items() if changed_analysis['hex_name'] in h_list for gn in liuyao.GENERATION_NAMES if h_list.index(changed_analysis['hex_name']) == liuyao.GENERATION_NAMES.index(gn)]
                changed_analysis['gen_name'] = gen_name_list[0] if gen_name_list else '未知'
                if changed_analysis:
                    changed_analysis['moving_lines_in_main'] = moving_lines # For LLM formatting

        interpretation_details = liuyao.get_interpretation_details(main_analysis, day_branch, month_branch)

        day_info_str = f"分析日期 ({input_date or datetime.date.today()}) 為「{day_stem}{day_branch}」日，日干五行屬【{day_element}】，月建為【{month_branch}】，空亡為【{'、'.join(empty_branches)}】"
        
        llm_formatted_data = liuyao.format_for_llm(main_analysis, changed_analysis, interpretation_details, day_info_str, question)
        
        # Select prompt based on category
        if category == "relationship":
            prompt = generate_marriage_prompt(question, main_analysis, changed_analysis, interpretation_details, day_info_str)
        elif category == "career":
            # Retrieve Yilin verse
            yilin_data = parse_sql_file()
            yilin_verse = None
            if changed_analysis and changed_analysis.get('hex_name'):
                # Find verse for main hexagram changing to changed hexagram
                for entry in yilin_data:
                    if entry['from'] == main_analysis['hex_name'] and entry['to'] == changed_analysis['hex_name']:
                        yilin_verse = entry
                        break
            if not yilin_verse: # If no changing hexagram or no specific verse found, try main hexagram to itself
                for entry in yilin_data:
                    if entry['from'] == main_analysis['hex_name'] and entry['to'] == main_analysis['hex_name']:
                        yilin_verse = entry
                        break

            prompt = generate_career_prompt(question, main_analysis, changed_analysis, interpretation_details, day_info_str, yilin_verse)
        else: # Default to general interpretation
            prompt = liuyao.LLM_PROMPT_TEMPLATE + "\n\n" + llm_formatted_data

        gemini_interpretation_html = call_gemini_api(prompt)

        if user and "呼叫 Gemini API 時出錯" not in gemini_interpretation_html:
            send_liuyao_email(question, input_date, day_info_str, main_analysis, changed_analysis, moving_lines, interpretation_details, gemini_interpretation_html, {'username': user.username})

        # Update usage count (if implemented)
        user.usage_count += 1
        db.session.commit()

        return render_template("liuyao_result.html",
                               question=question,
                               input_date=input_date,
                               day_info_str=day_info_str,
                               main_analysis=main_analysis,
                               changed_analysis=changed_analysis,
                               moving_lines=moving_lines,
                               interpretation_details=interpretation_details,
                               gemini_interpretation=gemini_interpretation_html)

    return render_template("liuyao.html")

@app.route('/yilin_index')
@login_required
@admin_required
@log_request
def yilin_index():
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

    return render_template('yilin_index.html', from_hexagrams=from_hexagrams, hex_info=HEX_INFO)

@app.route('/yilin_hexagram/<from_hex>')
@login_required
@log_request
def yilin_hexagram_details(from_hex):
    data = parse_sql_file()

    self_verse_entry = None
    other_verses = []
    for entry in data:
        if entry['from'] == from_hex:
            if entry['to'] == from_hex:
                self_verse_entry = entry
            else:
                other_verses.append(entry)

    return render_template('yilin_details.html',
                                  from_hex=from_hex,
                                  self_verse_entry=self_verse_entry,
                                  verses=other_verses)

@app.route('/yilin_edit/<from_hex>/<to_hex>', methods=['GET', 'POST'])
@login_required
@log_request
def yilin_edit_verse(from_hex, to_hex):
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
        return redirect(url_for('yilin_hexagram_details', from_hex=from_hex))

    return render_template('yilin_edit.html', from_hex=from_hex, to_hex=to_hex, verse=entry_to_edit['verse'])

@app.route('/yilin_fate_calculator', methods=['GET', 'POST'])
@login_required
@admin_required
@log_request
def yilin_fate_calculator():
    result = None
    solar_term = None
    input_date_str = datetime.datetime.now().strftime("%Y-%m-%d") # Use a different variable name to avoid conflict

    if request.method == 'POST':
        input_date_str = request.form.get('date')
        if not input_date_str:
            input_date_str = datetime.datetime.now().strftime("%Y-%m-%d")

        try:
            datetime.datetime.strptime(input_date_str, "%Y-%m-%d")
            result, solar_term = get_hex(input_date_str)
        except ValueError:
            flash("日期格式錯誤，請使用 YYYY-MM-DD 格式。")
            return render_template('yilin_fate_calculator.html', result=None, solar_term=None, input_date=input_date_str)
        except Exception as e:
            flash(str(e))
            return render_template('yilin_fate_calculator.html', result=None, solar_term=None, input_date=input_date_str)

    return render_template('yilin_fate_calculator.html', result=result, solar_term=solar_term, input_date=input_date_str)

@app.route("/download_pdf/<result_id>")
@login_required
@log_request
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

@app.errorhandler(500)
def internal_server_error(e):
    # For API requests, return a JSON error response
    if request.path.startswith('/api/'):
        return jsonify({"error": "內部伺服器錯誤", "message": "伺服器發生未知錯誤，請稍後再試。"}), 500
    # For non-API requests, you might want to render a custom error page
    # For now, we'll just return a generic message
    return "<h1>500 Internal Server Error</h1><p>伺服器發生未知錯誤，請稍後再試。</p>", 500

# 使用 app context 來建立資料庫表格
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)