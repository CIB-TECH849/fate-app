import os
from pdfminer.high_level import extract_text

PDF_FILE_PATH = "C:\\fate\\yi_ching.pdf"

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts all text from a PDF file using pdfminer.six.
    """
    try:
        text = extract_text(pdf_path)
    except FileNotFoundError:
        return f"錯誤：找不到檔案 {pdf_path}"
    except Exception as e:
        return f"讀取 PDF 檔案時發生錯誤: {e}"
    return text

if __name__ == "__main__":
    print(f"正在從 {PDF_FILE_PATH} 提取文字內容 (使用 pdfminer.six)...")
    extracted_text = extract_text_from_pdf(PDF_FILE_PATH)
    
    if extracted_text.startswith("錯誤"):
        print(extracted_text)
    else:
        # Save the extracted text to a file for review
        output_file_path = "C:\\fate\\extracted_yi_ching_text.txt"
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(extracted_text)
        print(f"文字內容已成功提取並儲存至 {output_file_path}")
        print("\n請檢查 extracted_yi_ching_text.txt 檔案，確認文字提取的品質。")
        print("根據提取的文字內容，我們才能進一步規劃如何解析資料並建立資料庫。")