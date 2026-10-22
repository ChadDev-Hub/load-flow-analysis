from .generator import DSAS_TEMPLATE_GENERATOR
from sqlalchemy import text, Engine
import re

class SecondaryLines(DSAS_TEMPLATE_GENERATOR):
    def __init__(self, substation_id, billing_period, db_engine:Engine):
        super().__init__(substation_id, billing_period, db_engine)
    def classify_installation_type(self, description):
        if re.match(r"(UNDER-*BUILT)", description, re.IGNORECASE):
            return 1
        elif re.match(r"(OPEN-*SECONDARY)", description, re.IGNORECASE):
            return 2
        else: 
            return 0
            
    
    def save_secondary_lines(self):
        secondary_lines = self.read_process_secondary_lines()
        secondary_lines['installation_type'] = secondary_lines['description'].apply(lambda x: self.classify_installation_type(x))
        secondary_lines = secondary_lines[['secondary_line_id', 'from_bus_id',
       'to_bus_id', 'phasing', 'installation_type', 'length_meters',
       'type', 'size', 'unit', 'strand']]
        return secondary_lines
    
    
    
