
# Temporary test code to verify date calculation
if __name__ == "__main__":
    test_date = datetime.date(2025, 10, 16)
    day_stem, day_branch, day_element, month_branch = get_day_info(test_date)
    empty_branches = get_kong_wang(day_stem, day_branch)
    print(f"Test Date: {test_date}")
    print(f"Day Stem-Branch: {day_stem}{day_branch}")
    print(f"Day Element: {day_element}")
    print(f"Month Branch: {month_branch}")
    print(f"Empty Branches: {empty_branches}")
