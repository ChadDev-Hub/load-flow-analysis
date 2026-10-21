from sqlalchemy import create_engine, text
import pandas as pd
import os
from dotenv import load_dotenv


load_dotenv()


engine = create_engine(os.getenv("DB_HOST"))

billing_data = r"kwh-data\kwh_2025.csv"
def update_consumer_type():
    df = pd.read_csv(billing_data)
    df = df.drop_duplicates(subset=['account_no'])
    
    df = df[['account_no', 'type']]
    df['account_no'] = df['account_no'].str.replace('-','').str.strip()
    
    
    update_tmt = text(
        """
        update gis.consumer_meter
        set account_type = :type
        where account_no = :account_no
        """
    )
    with engine.connect() as conn:
        conn.execute(update_tmt, df.to_dict(orient='records'))
        conn.commit()
    return "Update Completed"

if __name__ == "__main__":
    print(update_consumer_type())
