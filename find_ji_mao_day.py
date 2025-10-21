import datetime
from liuyao_system import get_day_info, HEAVENLY_STEMS, EARTHLY_BRANCHES

# Find the next Ji Mao day
if __name__ == "__main__":
    with open("ji_mao_date.txt", "w", encoding="utf-8") as f:
        target_stem = "己"
        target_branch = "卯"
        
        start_date = datetime.date(2025, 10, 16)
        day_count = 0
        while day_count < 60: # A full cycle
            current_date = start_date + datetime.timedelta(days=day_count)
            day_stem, day_branch, _, _ = get_day_info(current_date)
            if day_stem == target_stem and day_branch == target_branch:
                f.write(f"The next {target_stem}{target_branch} day is: {current_date}\n")
                break
            day_count += 1