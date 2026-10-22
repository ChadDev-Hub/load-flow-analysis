from .secondary_lines import SecondaryLines
from .generator import DSAS_TEMPLATE_GENERATOR
from .consumer_meter import ConsumerMeter
from .service_drop import ServiceDropWires
from sqlalchemy import Engine

class TemplateGenerator(
    DSAS_TEMPLATE_GENERATOR
):
    def __init__(self, substation_id, billing_period, db_engine:Engine):
        super().__init__(substation_id, billing_period, db_engine)
        
        self.consumer_meter = ConsumerMeter(self.substation_id, self.billing_period, self.db_engine)
        self.secondary_lines = SecondaryLines(self.substation_id, self.billing_period, self.db_engine)
        self.service_drop = ServiceDropWires(self.substation_id, self.billing_period, self.db_engine)