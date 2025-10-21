
import datetime
from liuyao_system import get_day_info, get_kong_wang

# Temporary test code to verify date calculation
if __name__ == "__main__":
    with open("date_calculation_output.txt", "w", encoding="utf-8") as f:
        test_date = datetime.date(2025, 10, 15)
        day_stem, day_branch, day_element, month_branch = get_day_info(test_date)
        empty_branches = get_kong_wang(day_stem, day_branch)
        f.write(f"Test Date: {test_date}\n")
        f.write(f"Day Stem-Branch: {day_stem}{day_branch}\n")
        f.write(f"Day Element: {day_element}\n")
        f.write(f"Month Branch: {month_branch}\n")
        f.write(f"Empty Branches: {empty_branches}\n")
