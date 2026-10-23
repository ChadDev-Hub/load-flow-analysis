
from .generator import DSAS_TEMPLATE_GENERATOR
from sqlalchemy import Engine
import os
class BusData(DSAS_TEMPLATE_GENERATOR):
    def __init__(self, substation_id, billing_period, db_engine:Engine):
        super().__init__(substation_id, billing_period, db_engine)
    
    def save_bus_data(self):
        bus = self.process_bus_data()
        bus.insert(0,'count', bus.index + 1)
        bus.drop(columns=['geom'], inplace=True)    
        return bus
    
    def generate_template(self, output_folder):
        complete = False
        try:
            bus = self.save_bus_data()
            bus.to_csv(os.path.join(output_folder,"bus.csv"), index=False)
            complete = True
        except Exception as e:
            print(e)
            complete = False
        finally:
            return complete
        