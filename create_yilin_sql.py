
import requests
from bs4 import BeautifulSoup
import re
import os

def create_yilin_sql():
    """
    Scrapes the Jiaoshi Yilin data from www.eee-learning.com and saves it to a SQL file.
    """
    base_url = "https://www.eee-learning.com/giaju/{}"
    sql_file_path = "yilin.sql"

    with open(sql_file_path, "w", encoding="utf-8") as f:
        f.write("CREATE TABLE yilin (\n")
        f.write("    from_hexagram TEXT,\n")
        f.write("    to_hexagram TEXT,\n")
        f.write("    verse TEXT\n")
        f.write(");\n\n")

    for i in range(1, 65):
        url = base_url.format(i)
        print(f"Scraping page {i}/64: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            continue

        soup = BeautifulSoup(response.content, "html.parser")

        title = soup.find("title").text
        from_hex_match = re.search(r"\d+\.\s*([^之]+)之", title)
        if not from_hex_match:
            print(f"Could not find 'from' hexagram in title: {title}")
            continue
        from_hex = from_hex_match.group(1)

        content_div = soup.find("div", class_="field--name-body")
        if not content_div:
            print(f"Could not find content div in {url}")
            continue

        strong_tags = content_div.find_all("strong")

        if not strong_tags:
            continue

        # Handle the first entry (from_hex to from_hex)
        first_verse = strong_tags[0].text.strip()
        append_to_sql(sql_file_path, from_hex, from_hex, first_verse)

        # Handle the rest of the entries
        for j in range(1, len(strong_tags)):
            strong_text = strong_tags[j].get_text(separator=' ', strip=True)
            
            # Try to match format "2. 之坤 ..."
            match = re.match(r"(\d+)\.\s*之(\S+)\s+(.*)", strong_text)
            if match:
                to_hex = match.group(2)
                verse = match.group(3).strip()
                append_to_sql(sql_file_path, from_hex, to_hex, verse)
                continue

            # Try to match format "3. 屯 ..."
            match = re.match(r"(\d+)\.\s*(\S+)\s+(.*)", strong_text)
            if match:
                to_hex = match.group(2)
                verse = match.group(3).strip()
                append_to_sql(sql_file_path, from_hex, to_hex, verse)

def append_to_sql(file_path, from_hex, to_hex, verse):
    """Appends a single INSERT statement to the SQL file."""
    with open(file_path, "a", encoding="utf-8") as f:
        # Escape single quotes for SQL
        verse = verse.replace("'", "''")
        f.write(f"INSERT INTO yilin (from_hexagram, to_hexagram, verse) VALUES ('{from_hex}', '{to_hex}', '{verse}');\n")

if __name__ == "__main__":
    create_yilin_sql()
    print(f"SQL file 'yilin.sql' created successfully.")
