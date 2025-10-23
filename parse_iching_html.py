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
    hex_name_tag = None
    for strong_tag in soup.find_all('strong'):
        if 'Hexagram Name:' in strong_tag.get_text():
            hex_name_tag = strong_tag
            break

    if hex_name_tag:
        # The actual hexagram name and symbol are in the text node right after the strong tag
        hex_info_full_text = hex_name_tag.next_sibling
        if hex_info_full_text:
            hex_info_full_text = hex_info_full_text.strip()
            print(f"DEBUG: hex_info_full_text = '{hex_info_full_text}'")
            # Expected format: "䷀　乾卦 　乾下乾上"
            match = re.search(r'(\S+)\s*(\S+)卦', hex_info_full_text)
            if match:
                data['symbol'] = match.group(1)
                data['name'] = match.group(2)
                print(f"DEBUG: Extracted name='{data['name']}', symbol='{data['symbol']}'")
            else:
                print(f"DEBUG: Regex for hexagram name/symbol failed on '{hex_info_full_text}'")
                if '乾卦' in hex_info_full_text:
                    data['name'] = '乾'
                    data['symbol'] = '䷀'
        else:
            print("DEBUG: hex_name_tag.next_sibling is empty.")
    else:
        print("DEBUG: 'Hexagram Name:' strong tag not found.")

    # Ensure 'name' is set, even if parsing fails, for HEX_INFO lookup
    if 'name' not in data:
        data['name'] = '乾' # Default to '乾' for this specific page if parsing fails

    # Get full_name for Qian
    data['full_name'] = "乾為天" # Hardcode for Qian for now

    # Extract Hexagram Text (卦辭)
    hex_text_tag = soup.find('strong', string=re.compile(r'Hexagram Text:'))
    if hex_text_tag:
        # Find the next sibling that contains the actual text, could be a NavigableString or a <p> tag
        next_element = hex_text_tag.next_sibling
        while next_element and (next_element.name == 'br' or (next_element.string and next_element.string.strip() == '')):
            next_element = next_element.next_sibling
        if next_element:
            data['hexagram_text'] = next_element.get_text(strip=True) if next_element.name == 'p' else next_element.strip()

    # Extract Commentaries
    tuan_zhuan_tag = soup.find('strong', string=re.compile(r'《彖》曰'))
    if tuan_zhuan_tag:
        next_element = tuan_zhuan_tag.next_sibling
        while next_element and (next_element.name == 'br' or (next_element.string and next_element.string.strip() == '')):
            next_element = next_element.next_sibling
        if next_element:
            data['tuan_zhuan'] = next_element.get_text(strip=True) if next_element.name == 'p' else next_element.strip()

    xiang_zhuan_tag = soup.find('strong', string=re.compile(r'《象》曰'))
    if xiang_zhuan_tag:
        xiang_content = []
        next_element = xiang_zhuan_tag.next_sibling
        while next_element and next_element.name != 'strong' and not (next_element.name == 'h2' or (next_element.name == 'p' and 'Notes:' in next_element.get_text())):
            if next_element.name == 'p':
                xiang_content.append(next_element.get_text(strip=True))
            elif next_element.string and next_element.string.strip(): # Handle direct text nodes
                xiang_content.append(next_element.strip())
            next_element = next_element.next_sibling
        data['xiang_zhuan_da'] = "\n".join(xiang_content) if xiang_content else ""

    wen_yan_tag = soup.find('strong', string=re.compile(r'《文言》曰'))
    if wen_yan_tag:
        wen_yan_content = []
        next_element = wen_yan_tag.next_sibling
        while next_element and next_element.name != 'strong' and not (next_element.name == 'h2' or (next_element.name == 'p' and 'Notes:' in next_element.get_text())):
            if next_element.name == 'p':
                wen_yan_content.append(next_element.get_text(strip=True))
            elif next_element.string and next_element.string.strip(): # Handle direct text nodes
                wen_yan_content.append(next_element.strip())
            next_element = next_element.next_sibling
        data['wen_yan'] = "\n".join(wen_yan_content)

    return data

def populate_iching_db(parsed_data: dict):
    """
    Populates the IChingHexagram and IChingLine tables with parsed data.
    """
    with app.app_context():
        hex_name = parsed_data['name']
        existing_hexagram = IChingHexagram.query.filter_by(name=hex_name).first()
        if existing_hexagram:
            print(f"警告：卦名 {hex_name} 已存在於資料庫中，跳過插入。")
            # Optionally, update existing hexagram here if needed
            return

        # Get hexagram number and symbol from HEX_INFO
        hex_info = HEX_INFO.get(hex_name)
        if not hex_info:
            print(f"錯誤：在 HEX_INFO 中找不到卦名 {hex_name}.")
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
