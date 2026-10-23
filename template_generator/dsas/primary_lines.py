from .generator import DSAS_TEMPLATE_GENERATOR
from sqlalchemy import  Engine
import os
class PrimaryLines(DSAS_TEMPLATE_GENERATOR):
    def __init__(self, substation_id, billing_period, db_engine: Engine):
        super().__init__(substation_id, billing_period, db_engine)

    def save_primary_line_overhead(self):
        primary_lines = self.process_primary_lines()
        primary_lines.insert(0, 'count', primary_lines.index + 1)
        primary_line_overhead = primary_lines[primary_lines['description']
                                              == 'PRIMARY LINE OVERHEAD']
        primary_line_overhead = primary_line_overhead[
            ['count',  'primary_line_id', 'from_bus_id', 'to_bus_id',
             'phasing', 'configuration', 'system_ground_type',
             'length_meters', 'conductor_type',
             'conductor_size', 'conductor_unit', 'conductor_strand', 'neutral_type',
             'neutral_size', 'neutral_unit','neutral_strand', 'spacing_d12_meters',
             'spacing_d23_meters', 'spacing_d13_meters', 'spacing_d1n_meters',
             'spacing_d2n_meters', 'spacing_d3n_meters', 'spacing_dc1_c2_meters',
             'height_h1_meters', 'height_h2_meters', 'height_h3_meters',
             'height_hn_meters', 'earth_resistivity_ohm_meter']]
        return primary_line_overhead

    def save_primary_line_underground(self):
        primary_lines = self.process_primary_lines()
        primary_lines.insert(0, 'count', primary_lines.index + 1)
        primary_line_underground = primary_lines[primary_lines['description']
                                                 == 'PRIMARY LINE UNDERGROUND']
        
        primary_line_underground = primary_line_underground[[
            'count',  'primary_line_id', 'from_bus_id', 'to_bus_id',
            'phasing',
            'length_meters', 'conductor_type',
            'conductor_size', 'conductor_unit']]
        primary_line_underground['count'] = 1
        primary_line_underground['no_of_cores'] = 1
        primary_line_underground['diameter_underarmour'] = 43.82
        primary_line_underground['armour_wire_diameter']= 0.10
        primary_line_underground['overall_diameter'] = 49.60
        primary_line_underground['ac_resistance_ohm_per_meter'] = 0.09
        primary_line_underground['inductive_resistance'] = 0.25
        primary_line_underground['capacitant'] = 0.22
        primary_line_underground['earth_resistivity_ohm_meter'] = 100
        
        return primary_line_underground

    def save_pred_rel_data(self):
        primary_lines = self.process_primary_lines()
        pred_rel = primary_lines[['primary_line_id']]
        pred_rel['permanent_failure_rate'] = 0.3
        pred_rel['temporary_failure_rate'] = 0.3
        pred_rel['repair_rate_hour'] = 0.5
        pred_rel.insert(0, 'count', pred_rel.index + 1)
        return pred_rel
    
    def generate_template(self, output_folder):
        complete = False
        try:
            primary_line_overhead = self.save_primary_line_overhead()
            primary_line_overhead.to_csv(os.path.join(output_folder,"primary_line_overhead.csv"), index=False)
            primary_line_underground = self.save_primary_line_underground()
            primary_line_underground.to_csv(os.path.join(output_folder,"primary_line_underground.csv"), index=False)
            pred_rel = self.save_pred_rel_data()
            pred_rel.to_csv(os.path.join(output_folder,"pred_rel.csv"), index=False)
            complete = True
        except Exception as e:
            print(e)
            complete = False
        finally:
            return complete