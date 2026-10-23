from .generator import DSAS_TEMPLATE_GENERATOR
from sqlalchemy import text, Engine
import os
class DistributionTransformer(DSAS_TEMPLATE_GENERATOR):
    def __init__(self, substation_id, billing_period, db_engine:Engine):
        super().__init__(substation_id, billing_period, db_engine)
    def no_dts_classification(self, kva_rating, phasing):
        if kva_rating > 300 and len(phasing) == 4:
            return 3
        elif kva_rating <= 300 and len(phasing) == 4:
            return 4
        else:
            return 1
        
        
    def save_distribution_transformer_data(self):
        distribution_transformer = self.process_distribution_transformer()
        distribution_transformer['no_of_dts_in_bank'] = distribution_transformer.apply(lambda row: self.no_dts_classification(row['kva_rating'],row['primary_phasing']), axis=1)
        
        distribution_transformer['primary_tap_voltage_kv'] = distribution_transformer['primary_voltage_rating']
        distribution_transformer['secondary_tap_voltage_kv'] = distribution_transformer['secondary_voltage_rating']
        distribution_transformer = distribution_transformer[['transformer_id', 'from_primary_bus_id',
        'to_secondary_bus_id','primary_phasing', 'secondary_phasing','installation_type','no_of_dts_in_bank', 'connection_code','kva_rating',
       'primary_voltage_rating', 'secondary_voltage_rating', 'primary_tap_voltage_kv', 'secondary_tap_voltage_kv',
       '%Z',
       'X/R Ratio', 'No-Load Loss (kW)', 'Exciting Current (%)'
       ]]
        distribution_transformer.insert(0, 'count', distribution_transformer.index + 1)
        return distribution_transformer
    
    def generate_template(self, output_folder):
        complete = False
        try:
            distribution_transformer = self.save_distribution_transformer_data()
            distribution_transformer.to_csv(os.path.join(output_folder,"distribution_transformer.csv"), index=False)
            complete = True
        except Exception as e:
            print(e)
            complete = False
        finally:
            return complete