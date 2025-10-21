
import requests
from bs4 import BeautifulSoup
import json
import re

def get_yilin_data():
    """
    Scrapes the Jiaoshi Yilin data from www.eee-learning.com and saves it to a JSON file.
    """
    base_url = "https://www.eee-learning.com/giaju/{}"
    yilin_data = []

    for i in range(1, 65):
        print(f"Scraping page {i}/64...")
        url = base_url.format(i)
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for bad status codes
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            continue

        soup = BeautifulSoup(response.content, "html.parser")

        # Get the "from" hexagram from the title
        title = soup.find("title").text
        from_hex_match = re.search(r"\d+\.\s*([^之]+)之", title)
        if not from_hex_match:
            print(f"Could not find 'from' hexagram in title: {title}")
            continue
        from_hex = from_hex_match.group(1)

        # Find the correct content div
        content_div = soup.find("div", class_="field--name-body")
        if not content_div:
            print(f"Could not find content div in {url}")
            continue

        paragraphs = content_div.find_all("p")
        for p in paragraphs:
            # The first part of the text is in a <strong> tag, so get the whole text
            text = p.get_text(separator="\n").strip()
            lines = text.split("\n")
            if not lines:
                continue

            # The line with the hexagram transformation can be complex
            # e.g. <strong>2.&nbsp;<img ...>之坤...</strong>
            # The text we get from get_text() will have spaces and newlines.
            # Let's clean it up.
            cleaned_line = re.sub(r'\s+', ' ', lines[0]).strip()

            # Regex to find the hexagrams. It's tricky because of the html tags.
            # Let's try to find the pattern "之" and get the words around it.
            if '之' in cleaned_line:
                parts = cleaned_line.split('之')
                if len(parts) == 2:
                    # The first part contains the number and the from_hex.
                    # The second part contains the to_hex.
                    from_hex_part = parts[0]
                    to_hex_part = parts[1]

                    # Extract hexagram from to_hex_part
                    to_hex_match = re.search(r'([一-龥]+)', to_hex_part)
                    if to_hex_match:
                        to_hex = to_hex_match.group(1)

                        # The verse is in the following strong tag
                        verse_tag = p.find("strong", text=re.compile(f"{to_hex}"))
                        if verse_tag and verse_tag.next_sibling:
                            verse = verse_tag.next_sibling.strip()
                        else:
                            # Fallback for cases where the structure is different
                            if len(lines) > 1:
                                verse = "\n".join(lines[1:]).strip()
                            else:
                                verse = ""

                        yilin_data.append({
                            "from": from_hex,
                            "to": to_hex,
                            "verse": verse
                        })

    return yilin_data

if __name__ == "__main__":
    print("Starting to scrape Jiaoshi Yilin data...")
    data = get_yilin_data()
    if data:
        with open("yilin.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Successfully scraped {len(data)} entries and saved to yilin.json")
    else:
        print("No data was scraped.")
