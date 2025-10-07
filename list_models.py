# list_models.py

import os
import google.generativeai as genai

print("正在讀取環境變數中的 GEMINI_API_KEY...")
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("錯誤：請先設定名為 GEMINI_API_KEY 的環境變數。")
    genai.configure(api_key=api_key)

    print("成功設定 API 金鑰，正在查詢可用模型列表...")
    print("-"*20)

    for m in genai.list_models():
        # 我們只關心能用來生成內容的模型
        if 'generateContent' in m.supported_generation_methods:
            print(f"找到可用模型：{m.name}")

    print("-"*20)
    print("查詢完畢。")

except Exception as e:
    print(f"發生錯誤：{e}")
