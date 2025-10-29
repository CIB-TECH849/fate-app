import requests
from bs4 import BeautifulSoup
import re
import os
import sys

# Add the project root to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from web_app.app import app, db, IChingHexagram, IChingLine # Import app and db from your Flask app
from web_app.app import HEX_INFO # Import HEX_INFO for hexagram numbers and symbols
import liuyao_system as liuyao # Import liuyao_system for HEXAGRAM_MAP

# --- New function to parse a text block ---
def parse_iching_text_block(text_block: str) -> dict:
    """
    Parses a raw text block of I Ching data for a single hexagram.
    """
    data = {}

    # Hexagram Name and Full Name
    first_line = text_block.lstrip().split('\n')[0]
    name_match = re.search(r'(\S+)卦', first_line) # Match "乾卦"
    if name_match:
        data['name'] = name_match.group(1) # e.g., "乾"
        data['full_name'] = name_match.group(0) # e.g., "乾卦"
    else:
        print(f"DEBUG: Failed to extract hexagram name from first line: '{first_line}'")
        # Fallback if regex fails
        if '乾卦' in first_line:
            data['name'] = '乾'
            data['full_name'] = '乾卦'

    # Hexagram Text (卦辭)
    hex_text_match = re.search(r'乾，(.*?)\n', text_block)
    if hex_text_match:
        data['hexagram_text'] = hex_text_match.group(1).strip()

    # Line Texts (爻辭) and Xiao Xiang (小象) - This is complex, will simplify for now
    data['lines'] = []
    line_pattern = re.compile(r'^(初九|九二|九三|九四|九五|上九|用九)，(.*?)(?=\n*(?:初九|九二|九三|九四|九五|上九|用九|《)|$))', re.DOTALL)
    
    # Find all line matches
    line_matches = line_pattern.finditer(text_block)
    line_num_map = {
        '初九': 1, '九二': 2, '九三': 3, '九四': 4, '九五': 5, '上九': 6, '用九': 7
    }

    for match in line_matches:
        line_name = match.group(1)
        line_text_content = match.group(2).strip()
        line_number = line_num_map.get(line_name)
        data['lines'].append({
            'line_name': line_name,
            'line_number': line_number,
            'line_text': line_text_content,
            'xiang_zhuan_xiao': '' # Placeholder for now, needs more parsing
        })

    # Commentaries
    tuan_zhuan_match = re.search(r'《彖》曰.*?：(.*?)(?=\n*《象》曰)', text_block, re.DOTALL)
    if tuan_zhuan_match:
        data['tuan_zhuan'] = tuan_zhuan_match.group(1).strip()

    xiang_zhuan_match = re.search(r'《象》曰.*?：(.*?)(?=\n*《文言》曰)', text_block, re.DOTALL)
    if xiang_zhuan_match:
        xiang_content = xiang_zhuan_match.group(1).strip()
        # The first line is Da Xiang, subsequent lines are Xiao Xiang
        xiang_lines = xiang_content.split('\n')
        data['xiang_zhuan_da'] = xiang_lines[0].strip()
        # Xiao Xiang for each line needs to be matched to the line_text
        # This is complex and will be done in a later refinement.

    wen_yan_match = re.search(r'《文言》曰：(.*?)$', text_block, re.DOTALL)
    if wen_yan_match:
        data['wen_yan'] = wen_yan_match.group(1).strip()

    return data

def populate_iching_db(parsed_data: dict):
    """
    Populates the IChingHexagram and IChingLine tables with parsed data.
    """
    with app.app_context():
        hex_name = parsed_data['name']
        existing_hexagram = IChingHexagram.query.filter_by(name=hex_name).first()
        if existing_hexagram:
            print(f"警告：卦名 {hex_name} 已存在於資料庫中，跳過插入。\n")
            # Optionally, update existing hexagram here if needed
            return

        # Get hexagram number and symbol from HEX_INFO
        hex_info = HEX_INFO.get(hex_name)
        if not hex_info:
            print(f"錯誤：在 HEX_INFO 中找不到卦名 {hex_name}.\n")
            return

        hexagram = IChingHexagram(
            name=parsed_data['name'],
            full_name=parsed_data.get('full_name'),
            number=hex_info['number'],
            symbol=hex_info['symbol'],
            hexagram_text=parsed_data.get('hexagram_text'),
            tuan_zhuan=parsed_data.get('tuan_zhuan'),
            xiang_zhuan_da=parsed_data.get('xiang_zhuan_da'),
            wen_yan=parsed_data.get('wen_yan')
        )
        db.session.add(hexagram)
        db.session.commit() # Commit to get hexagram.id

        for line_data in parsed_data.get('lines', []):
            line = IChingLine(
                hexagram_id=hexagram.id,
                line_number=line_data['line_number'],
                line_name=line_data['line_name'],
                line_text=line_data['line_text'],
                # xiang_zhuan_xiao will need more specific parsing
                xiang_zhuan_xiao=''
            )
            db.session.add(line)
        db.session.commit()
        print(f"成功將 {parsed_data['name']} 卦資料寫入資料庫。\n")

if __name__ == "__main__":
    # The user provided this text block
    qian_text_block = """
乾卦 　乾下乾上　乾：音虔，剛健、強健也

乾，元亨利貞。

初九，潛龍勿用。

九二，見龍在田，利見大人。

九三，君子終日乾乾，夕惕若，厲，无咎[1]。

九四，或躍在淵，无咎。　无，古文無

九五，飛龍在天，利見大人。

上九，亢龍有悔。　　亢：音抗，高也。

用九，見群龍无首，吉。

《彖》曰[2]：大哉乾元，萬物資始，乃統天。

雲行雨施，品物流形。大明終始，六位時成，時乘六龍以御天。

乾道變化，各正性命，保合大和，乃利貞。　大和：太和也。

首出庶物，萬國咸寧。

《象》曰[3]：天行健，君子以自强不息[4]。

潛龍勿用，陽在下也。見龍在田，德施普也。

終日乾乾，反復道也。或躍在淵，進无咎也。

飛龍在天，大人造也。亢龍有悔，盈不可久也。

用九，天德不可為首也。

《文言》曰：元者善之長也，亨者嘉之會也，利者義之和也，貞者事之幹也。君子體仁足以長人，嘉會足以合禮，利物足以和義，貞固足以幹事。君子行此四德者，故曰：「乾，元亨利貞。」
"""
    print("正在解析乾卦文字內容...")
    parsed_qian_data = parse_iching_text_block(qian_text_block)

    if parsed_qian_data:
        populate_iching_db(parsed_qian_data)
    else:
        print("解析乾卦資料失敗。")