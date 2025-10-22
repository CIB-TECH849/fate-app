import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
API_ENDPOINT = "https://fate-app-xb48.onrender.com/api/meihua_divine"
# Get API Key from environment variable
API_KEY = os.environ.get("EXTERNAL_API_KEY")

if not API_KEY:
    print("錯誤：請在 .env 檔案中設定 EXTERNAL_API_KEY。")
    exit()

# --- Debugging: Print configuration ---
print(f"DEBUG: API_ENDPOINT = {API_ENDPOINT}")
print(f"DEBUG: API_KEY (partial) = {API_KEY[:4]}...{API_KEY[-4:]}") # Mask part of the key for security

# --- Function to make API request ---
def get_meihua_divination(question: str, num1: int, num2: int, num3: int):
    headers = {
        "X-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "question": question,
        "num1": num1,
        "num2": num2,
        "num3": num3
    }

    # Debugging: Print request details
    print(f"DEBUG: Request Headers = {headers}")
    print(f"DEBUG: Request Payload = {payload}")

    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload)
        
        # Debugging: Print raw response details before raising for status
        print(f"DEBUG: Raw Response Status Code = {response.status_code}")
        print(f"DEBUG: Raw Response Content = {response.text}")

        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API 請求失敗: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"回應狀態碼: {e.response.status_code}")
            print(f"回應內容: {e.response.text}")
        return None

# --- Example Usage ---
if __name__ == "__main__":
    print("--- 梅花易數 API 客戶端範例 ---")

    user_question = input("請輸入您的占卜問題：")
    
    while True:
        try:
            user_num1 = int(input("請輸入第一組數字 (100-999)："))
            user_num2 = int(input("請輸入第二組數字 (100-999)："))
            user_num3 = int(input("請輸入第三組數字 (100-999)："))
            if not (100 <= user_num1 <= 999 and 100 <= user_num2 <= 999 and 100 <= user_num3 <= 999):
                print("數字必須介於 100 到 999 之間，請重新輸入。")
                continue
            break
        except ValueError:
            print("無效的數字輸入，請輸入整數。")

    print("\n正在發送占卜請求，請稍候...")
    result = get_meihua_divination(user_question, user_num1, user_num2, user_num3)

    if result:
        print("\n--- 占卜結果 ---")
        print(f"問題: {result.get('question')}")
        print(f"數字: {result.get('numbers')}")
        print(f"本卦: {result.get('main_hexagram')} ({result.get('main_hexagram_judgement')})")
        print(f"互卦: {result.get('mutual_hexagram')} ({result.get('mutual_hexagram_judgement')})")
        print(f"變卦: {result.get('changing_hexagram')} ({result.get('changing_hexagram_judgement')})")
        print(f"動爻: {result.get('moving_line')}")
        print("\n--- AI 綜合解讀 ---")
        print(result.get('ai_interpretation_html'))
    else:
        print("\n未能獲取占卜結果。")