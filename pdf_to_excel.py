
import pdfplumber
import pandas as pd
import re

class Pdf_to_Excel:
    def __init__(self):
        pass
    def convert(self, pdf_path):
        pdf = pdfplumber.open(pdf_path)
        results = []
        for page in pdf.pages:
            text = page.extract_text()
            values = text.split('\n')[10:]
            pattern = r"\b[A-Za-z-]+,(?:\s[A-Za-z-]+)?"
            result = re.sub(pattern, "", values[6]).strip()
            result = re.sub(r"\s{2,}", " ", result)
            results.append(result.split(' '))
      
        return pd.DataFrame(results)



if __name__ == '__main__':
    pdf_to_excel = Pdf_to_Excel()
    df = pdf_to_excel.convert(r'kwh-data\2025\01 January.pdf')
    print(df)