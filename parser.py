import re

with open('output.txt', 'r', encoding='utf-8') as f:
    content = f.read()

content_match = re.search(r'Content:\n(.*)', content, re.DOTALL)
if not content_match:
    with open('parsed_output.txt', 'w', encoding='utf-8') as out_f:
        out_f.write("Content not found.")
    exit()

text = content_match.group(1)
start_index = text.find('乾宮卦')
if start_index != -1:
    text = text[start_index:]

palaces = ["乾", "震", "坎", "艮", "坤", "巽", "離", "兌"]

with open('parsed_output.txt', 'w', encoding='utf-8') as out_f:
    full_text = text
    for i, palace in enumerate(palaces):
        start_marker = f"{palace}宮卦"
        
        end_marker = ""
        if i + 1 < len(palaces):
            end_marker = f"{palaces[i+1]}宮卦"
        
        start_index = full_text.find(start_marker)
        if start_index == -1:
            continue
            
        end_index = -1
        if end_marker:
            end_index = full_text.find(end_marker, start_index)
        
        if end_index == -1:
            hexagrams_text = full_text[start_index + len(start_marker):]
        else:
            hexagrams_text = full_text[start_index + len(start_marker):end_index]

        hexagrams_text = hexagrams_text.strip()
        
        # Add markers for splitting
        hexagrams_text = hexagrams_text.replace("本宮卦", "|本宮卦: ")
        hexagrams_text = hexagrams_text.replace("一世卦", "|一世卦: ")
        hexagrams_text = hexagrams_text.replace("二世卦", "|二世卦: ")
        hexagrams_text = hexagrams_text.replace("三世卦", "|三世卦: ")
        hexagrams_text = hexagrams_text.replace("四世卦", "|四世卦: ")
        hexagrams_text = hexagrams_text.replace("五世卦", "|五世卦: ")
        hexagrams_text = hexagrams_text.replace("游魂卦", "|游魂卦: ")
        hexagrams_text = hexagrams_text.replace("歸魂卦", "|歸魂卦: ")
        hexagrams_text = hexagrams_text.replace("歸魂", "|歸魂卦: ") # Handle case where '卦' is missing
        
        hexagram_names = [name.strip() for name in hexagrams_text.split("|") if name.strip()]
        
        # Handle the known issue with "无妄"
        hexagram_names = [name.replace("?妄", "无妄") for name in hexagram_names]
        
        out_f.write(f"{palace}宮:\n")
        for name in hexagram_names:
            out_f.write(f"  {name}\n")
        out_f.write("\n")