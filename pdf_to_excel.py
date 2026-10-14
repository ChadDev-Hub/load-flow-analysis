
import pdfplumber
import pandas as pd
import re
import os
from tqdm import tqdm
class Pdf_to_Excel:
    def __init__(self):
        pass
    def convert(self, pdf_path):
        pdf = pdfplumber.open(pdf_path)
        results = []
        for page in tqdm(pdf.pages, "Extracting pages", unit="data"):
            text = page.extract_text()
            values = text.split('\n')[10:]
            for val in values:
                pattern = r"\b\d{2}-\d{4}-\d{4}\b|(?<![#\w.-])\d[\d,]*(?:\.\d+)?\b"
                result = re.findall(pattern,val)
                if len(result) < 5:
                    continue
                results.append(result[:4])
        df = pd.DataFrame(results, columns=['account_no', 'previous_reading', 'present_reading', 'kwh_used'])
        return df[:-1]



if __name__ == '__main__':
    pdf_to_excel = Pdf_to_Excel()
    pdf_path = r"kwh-data/2025"
    list_of_pdf = os.listdir(pdf_path)
    for pdf in list_of_pdf:
        pdf_number = pdf.split(' ')[0]
        pdf_month = pdf.split(' ')[1]
        path  = os.path.join(pdf_path, pdf)
        print("converting", pdf)
        df = pdf_to_excel.convert(path)
        year = '2025'
        result_dir = 'converted_kwr'
        os.makedirs(os.path.join(result_dir, year), exist_ok=True)
        distination_path = os.path.join(result_dir, year,f"{year}{pdf_number}.csv")
        df.to_csv(distination_path, index=False)
    