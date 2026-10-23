from .generator import DSAS_TEMPLATE_GENERATOR
from sqlalchemy import text, Engine
import os

class SimulationParameter(DSAS_TEMPLATE_GENERATOR):
    def __init__(self, substation_id, billing_period, db_engine:Engine):
        super().__init__(substation_id, billing_period, db_engine)
        
        
    def save_simulation_parameters(self, feeder_name):
        bus_data = self.process_bus_data()
        simulation_params = self.process_simulation_parameter()
        simulation_params.insert(0, 'feeder_root_bus', bus_data.loc[bus_data['description'] == 'Feeder Node']['bus_id'].values[0])
        simulation_params.insert(0, 'feeder_name', feeder_name)
        simulation_params.drop(columns = ['substation_id'], inplace=True)
        simulation_params = simulation_params.transpose().reset_index()
        simulation_params.columns = ['parameter', 'value']
        return simulation_params
        
    def generate_template(self, output_folder):
        complete = False
        try:
            simulation_params = self.save_simulation_parameters(self.substation_id)
            simulation_params.to_csv(os.path.join(output_folder,"simulation_parameters.csv"), index=False)
            complete = True
        except Exception as e:
            print(e)
            complete = False
        finally:
            return complete
