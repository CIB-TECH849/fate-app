
import re
import json
from bs4 import BeautifulSoup

def parse_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    hexagram_data = {}

    # Split content by major headings
    sections = re.split(r'【(.*?)】', content)

    i = 1
    while i < len(sections):
        heading = sections[i].strip()
        section_content = sections[i+1]
        i += 2

        if heading == "卦名":
            soup_section = BeautifulSoup(section_content, 'html.parser')
            strong_tag = soup_section.find('strong')
            if strong_tag:
                names_text = strong_tag.get_text()
                names = re.split(r'\s*　\s*', names_text)
                names_dict = {}
                for name in names:
                    if '：' in name:
                        key, value = name.split('：', 1)
                        names_dict[key.strip()] = value.strip()
                hexagram_data['卦名'] = names_dict

        elif heading == "卦義":
            soup_section = BeautifulSoup(section_content, 'html.parser')
            hexagram_data['卦義'] = soup_section.get_text().strip()

        elif heading == "經文註解":
            lines_data = {}
            # A more robust regex to capture each line section
            line_matches = re.findall(r'<p id="ch1_(\d+)">(.*?)</p>(.*?)<p>【今解】(.*?)</p>', section_content, re.DOTALL)

            for match in line_matches:
                line_num = int(match[0])
                line_text = BeautifulSoup(match[1], 'html.parser').get_text().strip()
                
                annotations_html = match[2]
                soup_annotations = BeautifulSoup(annotations_html, 'html.parser')
                annotations = []
                for li in soup_annotations.find_all('li'):
                    annotations.append(li.get_text().strip())

                interpretation = match[3].strip()

                lines_data[f'line_{line_num}'] = {
                    'text': line_text,
                    'annotations': annotations,
                    'interpretation': interpretation
                }
            hexagram_data['經文註解'] = lines_data

        elif heading == "彖傳注":
            soup_section = BeautifulSoup(section_content, 'html.parser')
            hexagram_data['彖傳注'] = soup_section.get_text().strip()

    return hexagram_data

if __name__ == '__main__':
    parsed_data = parse_data('data.txt')
    with open('iching_database.json', 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=4)
