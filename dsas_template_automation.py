
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
BILLING_PERIOD = "202501"
SUBSTATION_ID = ["CIPC0001"]



if __name__ == "__main__":
    template_generator = TemplateGenerator(SUBSTATION_ID, BILLING_PERIOD, engine)
    secondary_lines = template_generator.secondary_lines.save_secondary_lines()
    secondary_service_drop = template_generator.service_drop.secondary_service_drop()
    primary_service_drop = template_generator.service_drop.primary_service_drop()
    print(primary_service_drop)