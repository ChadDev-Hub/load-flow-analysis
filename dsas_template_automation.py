
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
load_dotenv()
import pandas as pd
pd.options.display.float_format = '{:,.2f}'.format
pd.options.display.max_columns = None
from template_generator.dsas.template_generator import TemplateGenerator

# ENGINES

DB_HOST = os.getenv("DB_HOST")
engine = create_engine(DB_HOST)
YEAR = "2025"
SUBSTATION_ID = ["CIPC0001"]



if __name__ == "__main__":
    BILLING_PERIODS = [f"{YEAR}{str(m).zfill(2)}" for m in range(1, 13)]
    for BILLING_PERIOD in BILLING_PERIODS:
        output_folder = os.path.join(os.getcwd(), "dsas_templates","coron_busuanga", "2025", BILLING_PERIOD)
        template_generator = TemplateGenerator(SUBSTATION_ID, BILLING_PERIOD, engine)
        template_generator.generate_all_templates(output_folder)
    

    
        