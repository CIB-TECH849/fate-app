
import re
import os

def parse_hexagram_page(text):
    data = {}
    try:
        # --- Basic Info ---
        # Assume the first line contains the hexagram number and name
        first_line = text.split('\n', 1)[0]
        match = re.search(r"(\d+)\s*.*?\s*(\S+為\S+)", text)
        if not match:
             match = re.search(r"【周易全解】\s*(\d+)\s*(\S+)", text)
             if not match:
                print("Error: Could not find hexagram number and name in the first line.")
                return None
             hex_num, full_name = match.groups()
             name = full_name[0]
        else:
            hex_num, full_name = match.groups()
            name = full_name[0]

        data['number'] = int(hex_num)
        data['name'] = name
        data['full_name'] = full_name

        # --- Judgment and Commentaries ---
        # Find text between 【經文註解】 and the first line (e.g., 初九)
        # This is brittle, but it's the best we can do with the text.
        judgment_block_match = re.search(r"【經文註解】(.*?)<p id=\"ch1_1\">", text, re.DOTALL)
        if not judgment_block_match:
            print("Error: Could not find the main judgment block.")
            return None
        
        judgment_block = judgment_block_match.group(1)
        
        judgment_match = re.search(r'<strong>(.*?)<\/strong>', judgment_block)
        judgment_text = judgment_match.group(1).strip() if judgment_match else ""

        tuan_match = re.search(r"《彖》曰：(.*?)(?:<\/span>|<\/p>)", judgment_block, re.DOTALL)
        xiang_match = re.search(r"《象》曰：(.*?)(?:<\/span>|<\/p>)", judgment_block, re.DOTALL)

        data['judgment'] = {
            "text": judgment_text,
            "tuan_commentary": tuan_match.group(1).strip().replace('\n',' ') if tuan_match else "",
            "xiang_commentary": xiang_match.group(1).strip().replace('\n',' ') if xiang_match else ""
        }

        # --- Lines ---
        lines = {}
        line_sections = re.split(r'<p id="ch1_\d+"><strong>', text)
        
        for section in line_sections[1:]:
            line_title_match = re.search(r'(.*?)(?:<\/strong>|<\/p>)', section)
            if not line_title_match: continue
            line_title_full = line_title_match.group(1).strip()

            parts = [p.strip() for p in line_title_full.split('，') if p.strip()]
            if not parts: continue

            line_name = parts[0]
            line_text = '，'.join(parts[1:])

            line_xiang_match = re.search(r"《象》曰：(.*?)(?:<\/span>|<\/p>)", section, re.DOTALL)
            line_xiang = line_xiang_match.group(1).strip().replace('\n',' ') if line_xiang_match else ""
            
            line_num_map = {"初": 1, "二": 2, "三": 3, "四": 4, "五": 5, "上": 6, "用": 9}
            line_num = line_num_map.get(line_name[0])

            if line_num:
                lines[str(line_num)] = {
                    "name": line_name,
                    "text": line_text,
                    "commentary": line_xiang
                }
        data['lines'] = lines
        return data

    except Exception as e:
        print(f"Error during parsing: {e}")
        return None

def run_parser():
    input_file = 'data.txt'
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.strip():
        print("Error: data.txt is empty.")
        return

    print(f"Parsing content from {input_file}...")
    hex_data = parse_hexagram_page(content)

    if hex_data and 'number' in hex_data:
        filename = f"{hex_data['number']}-{hex_data['name']}.txt"
        output_string = []
        output_string.append(f"卦號: {hex_data['number']}")
        output_string.append(f"卦名: {hex_data['name']}")
        output_string.append(f"全名: {hex_data['full_name']}")
        output_string.append("\n【卦辭】")
        output_string.append(hex_data['judgment']['text'])
        output_string.append(f"《彖》曰：{hex_data['judgment']['tuan_commentary']}")
        output_string.append(f"《象》曰：{hex_data['judgment']['xiang_commentary']}")
        output_string.append("\n---\n【爻辭】")

        sorted_lines = sorted(hex_data['lines'].items(), key=lambda item: int(item[0]))

        for i, line_data in sorted_lines:
            output_string.append(f"\n{line_data['name']}: {line_data['text']}")
            output_string.append(f"《象》曰：{line_data['commentary']}")

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("\n".join(output_string))
        print(f"Successfully created file: {filename}")

    else:
        print("  Failed to parse the provided content.")

if __name__ == '__main__':
    run_parser()
