from .secondary_lines import SecondaryLines
from .generator import DSAS_TEMPLATE_GENERATOR
from .consumer_meter import ConsumerMeter
from .service_drop import ServiceDropWires
from .bus import BusData
from .primary_lines import PrimaryLines
from .distribution_transformer import DistributionTransformer
from .simulation_params import SimulationParameter
from sqlalchemy import Engine
import os
from tqdm import tqdm
class TemplateGenerator(
    DSAS_TEMPLATE_GENERATOR
):
    def __init__(self, substation_id, billing_period, db_engine:Engine):
        super().__init__(substation_id, billing_period, db_engine)
        
        self.consumer_meter = ConsumerMeter(self.substation_id, self.billing_period, self.db_engine)
        self.secondary_lines = SecondaryLines(self.substation_id, self.billing_period, self.db_engine)
        self.service_drop = ServiceDropWires(self.substation_id, self.billing_period, self.db_engine)
        self.bus = BusData(self.substation_id, self.billing_period, self.db_engine)
        self.distribution_transformer = DistributionTransformer(self.substation_id, self.billing_period, self.db_engine)
        self.primary_lines = PrimaryLines(self.substation_id, self.billing_period, self.db_engine)
        self.simulation = SimulationParameter(self.substation_id, self.billing_period, self.db_engine)
        
        
        # ALL TEMPLATES
        self.templates = [
            self.simulation,
            self.consumer_meter,
            self.secondary_lines,
            self.service_drop,
            self.bus,
            self.distribution_transformer,
            self.primary_lines
        ]
        
    def generate_all_templates(self, output_folder):
        os.makedirs(output_folder, exist_ok=True)
        for template in tqdm(self.templates, desc=f"Generating {self.billing_period} Templates", ascii=True):
            template.generate_template(output_folder)
          