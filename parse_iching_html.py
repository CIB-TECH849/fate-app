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

def parse_qian_hexagram_page(url: str) -> dict:
    """
    Fetches and parses the content of the Qian Hexagram page.
    """
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print(f"錯誤：無法獲取網頁內容: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    data = {}

    # Extract Hexagram Name and Symbol
    hex_name_tag = soup.find('strong', string=re.compile(r'Hexagram Name:'))
    if hex_name_tag:
        hex_name_text = hex_name_tag.next_sibling.strip()
        match = re.search(r'(\S+)\s*(\S+)', hex_name_text)
        if match:
            data['name'] = match.group(2).replace('卦', '') # e.g., "乾"
            data['symbol'] = match.group(1) # e.g., "䷀"
        else:
            data['name'] = hex_name_text.replace('卦', '')
            data['symbol'] = ''

    # Get full_name for Qian
    data['full_name'] = "乾為天" # Hardcode for Qian for now

    # Extract Hexagram Text (卦辭)
    hex_text_tag = soup.find('strong', string=re.compile(r'Hexagram Text:'))
    if hex_text_tag:
        data['hexagram_text'] = hex_text_tag.next_sibling.strip()

    # Extract Line Texts (爻辭) and Xiao Xiang (小象)
    data['lines'] = []
    line_texts_tag = soup.find('strong', string=re.compile(r'Line Texts:'))
    if line_texts_tag:
        ul_tag = line_texts_tag.find_next_sibling('ul')
        if ul_tag:
            line_num_map = {
                '初九': 1, '九二': 2, '九三': 3, '九四': 4, '九五': 5, '上九': 6, '用九': 7
            }
            for li in ul_tag.find_all('li'):
                line_text_content = li.get_text(strip=True)
                line_name_match = re.match(r'(\S+)，', line_text_content)
                if line_name_match:
                    line_name = line_name_match.group(1)
                    line_number = line_num_map.get(line_name)
                    data['lines'].append({
                        'line_name': line_name,
                        'line_number': line_number,
                        'line_text': line_text_content,
                        'xiang_zhuan_xiao': '' # Placeholder for now
                    })

    # Extract Commentaries
    tuan_zhuan_tag = soup.find('strong', string=re.compile(r'《彖》曰'))
    if tuan_zhuan_tag:
        data['tuan_zhuan'] = tuan_zhuan_tag.next_sibling.strip()

    xiang_zhuan_tag = soup.find('strong', string=re.compile(r'《象》曰'))
    if xiang_zhuan_tag:
        xiang_content = []
        current_tag = xiang_zhuan_tag.next_sibling
        while current_tag and current_tag.name != 'strong' and not current_tag.name == 'h2': # Stop before next strong tag or h2
            if current_tag.name == 'p':
                xiang_content.append(current_tag.get_text(strip=True))
            current_tag = current_tag.next_sibling
        data['xiang_zhuan_da'] = xiang_content[0] if xiang_content else "" # Assuming first paragraph is Da Xiang

    wen_yan_tag = soup.find('strong', string=re.compile(r'《文言》曰'))
    if wen_yan_tag:
        wen_yan_content = []
        current_tag = wen_yan_tag.next_sibling
        while current_tag and current_tag.name != 'strong' and not current_tag.name == 'h2':
            if current_tag.name == 'p':
                wen_yan_content.append(current_tag.get_text(strip=True))
            current_tag = current_tag.next_sibling
        data['wen_yan'] = "\n".join(wen_yan_content)

    return data

def populate_iching_db(parsed_data: dict):
    """
    Populates the IChingHexagram and IChingLine tables with parsed data.
    """
    with app.app_context():
        # Get hexagram number and symbol from HEX_INFO
        hex_info = HEX_INFO.get(parsed_data['name'])
        if not hex_info:
            print(f"錯誤：在 HEX_INFO 中找不到卦名 {parsed_data['name']}")
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
                xiang_zhuan_xiao=""
            )
            db.session.add(line)
        db.session.commit()
        print(f"成功將 {parsed_data['name']} 卦資料寫入資料庫。")

if __name__ == "__main__":
    QIAN_URL = "https://www.eee-learning.com/book/eee1"
    print(f"正在從 {QIAN_URL} 獲取並解析乾卦資料...")
    parsed_qian_data = parse_qian_hexagram_page(QIAN_URL)

    if parsed_qian_data:
        populate_iching_db(parsed_qian_data)
    else:
        print("解析乾卦資料失敗。")
