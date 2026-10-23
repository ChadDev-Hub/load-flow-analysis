import pandas as pd
from sqlalchemy import Engine, text
import re
from template_generator.dsas.generator import DSAS_TEMPLATE_GENERATOR
from datetime import datetime
import calendar
import os
class ConsumerMeter(DSAS_TEMPLATE_GENERATOR):
    def __init__(self, substation_id, billing_period, db_engine:Engine):
        super().__init__(substation_id, billing_period, db_engine)

    def type_classification(self, customer_type, kwh_used):
        """
            Classify customer type
        Args:
            customer_type (_type_): billing consumer type
            kwh_used (_type_): consumer kwh

        Returns:
            _type_: literal[RES1, RES2, RES3, COM1, COM2, COM3]
        """
        if re.match(r"(CIPC|NPC)\s*R" , customer_type, re.IGNORECASE):
            if kwh_used <= 50:
                return "RES1" 
            elif kwh_used <= 150:
                return "RES2"
            elif kwh_used <= 300:
                return "RES3"
            elif kwh_used > 300:
                return "RES4"
        elif re.match(r"(NPC|CIPC)\s+(SC|LC)" , customer_type, re.IGNORECASE):
            if kwh_used <= 300:
                return "COM1"
            elif kwh_used <= 800:
                return "COM2"
            elif kwh_used <= 2500:
                return "COM3"
            elif kwh_used > 2500:
                return "COM4"
        elif re.match(r"(NPC|CIPC)\s+PB" , customer_type, re.IGNORECASE):
            if kwh_used <= 800:
                return "PB1"
            elif kwh_used > 800:
                return "PB2"
        elif re.match(r"(NPC|CIPC)\s+SL" , customer_type, re.IGNORECASE):
            return "SL"
        elif re.match(r"(NPC|CIPC)\s+(I|O)" , customer_type, re.IGNORECASE):
            return "IND"
        elif re.match(r"Consumer\s*Lump" , customer_type, re.IGNORECASE):
            return "RES2"
        else:
            return customer_type
    
    def phase_classification(self, phasing):
        if len(phasing) == 2:
            return 1
        elif len(phasing) == 3:
            return 2
        elif len(phasing) == 4:
            return 3
        else:
            return phasing
    
    # CUSTOMER DATA
    def save_customer_data(self):
        consumer = self.read_and_process_consumer_meter()
        consumer['customer_type'] = consumer.apply(lambda x: self.type_classification(x['customer_type'], x['kwh_used']), axis=1)
        consumer['service_voltage'] = (consumer['nominal_voltage_kv'] * 1000).astype("int")
        consumer['phase'] = consumer.apply(lambda x: self.phase_classification(x['phasing']), axis=1)
        consumer = consumer[['customer_id', 'customer_name','customer_type', 'service_voltage', 'phase']]
        consumer.insert(0,'count', consumer.index + 1)
        return consumer
    
    
    # BILLING CYCLE
    def calculate_number_of_days(self):
        '''USING CALENDAR MODULE TO DETERMINE NUMBER OF DAYS IN MONTH'''
        period = datetime.strptime(self.billing_period, "%Y%m")
        number_of_days = calendar.monthrange(period.year, period.month)[1]
        return number_of_days
    
    def calculate_number_of_hours(self):
        '''USING CALENDAR MODULE TO DETERMINE NUMBER OF HOURS IN MONTH'''
        period = datetime.strptime(self.billing_period, "%Y%m")
        number_of_hours = calendar.monthrange(period.year, period.month)[1] * 24
        return number_of_hours
    
    def save_billing_cycle(self):
        '''save billing cycle template'''
        billing_cycle = {
            "count": 1, 
            "period": self.billing_period,
            "period_covered": datetime.strptime(self.billing_period, "%Y%m").strftime("%B %Y"),
            "number_of_days": self.calculate_number_of_days(),
            "number_of_hours": self.calculate_number_of_hours()
        }
        billing_cycle_df = pd.DataFrame(billing_cycle, index=[0])
        return billing_cycle_df
    # ---------------------------------------------------------------------------------------------
    # CUSTOMER ENERGY CONSUMPTION
    def status_classification(self, kwh_used):
        '''CLASSIFY CONSUMER STATUS based on the kwh used'''
        if kwh_used == 0:
            return 0
        else:
            return 1
    def save_customer_energy_consumption(self):
        consumer = self.read_and_process_consumer_meter()
        consumer['status'] = consumer['kwh_used'].apply(lambda x: self.status_classification(x))
        consumer['power_factor'] = 0.93
        consumer = consumer[['customer_id', 'billing_period', 'kwh_used', 'power_factor', 'status']]
        consumer.insert(0,'count', consumer.index + 1)
        return consumer
    
    
    def classify_load_curve(self): 
        if re.match(r'CIPC0001|NPCC0001',self.substation_id[0], re.IGNORECASE):
            return 'MAIN LAND'
        else:
            return 'ISLANDS'
    def load_curve_description(self):
        description = {
            'RES1': 'Low consumption residential kwh used < 300kwh',
            'RES2': 'Low consumption residential kwh used > 300kwh',
            'RES3': 'Medium consumption residential kwh used > 800kwh',
            'RES4': 'High consumption residential kwh used > 2500kwh',
            'COM1': 'Low consumption commercial kwh used < 300kwh',
            'COM2': 'Low consumption commercial kwh used > 300kwh',
            'COM3': 'Medium consumption commercial kwh used > 800kwh',
            'COM4': 'High consumption commercial kwh used > 2500kwh',
            'SL': 'Street Lights',
            'IND': 'Industrial',
            'PB1': 'low to medium consumption public building',
            'PB2': 'high consumption public building'
        }
        return description
        
    # LOAD CURVE DATA
    def save_load_curve_data(self):
        lcdf = pd.read_csv(r"surveyed-load-curve\load_curve.csv")
        used_load_curve = self.classify_load_curve()
        lcdf = lcdf.loc[lcdf['area'] == used_load_curve]
        lcdf.sort_values(by="customer_type", inplace=True)
        provider = re.search(r'[A-Za-z]*',self.substation_id[0]).group(0)
        lcdf.insert(1, 'load_curve_id', provider+lcdf['customer_type'])
        lcdf.drop(columns = ['id','area','max'], inplace=True)
        lcdf.insert(2, 'description', lcdf['customer_type'].map(self.load_curve_description()))
        lcdf.insert(0, 'count', lcdf.index + 1)
        return lcdf
    
    # GENERATE ALL TEMPLATES
    def generate_template(self, output_folder):
        complete = False
        try:
            customer = self.save_customer_data()
            billing_cycle = self.save_billing_cycle()
            customer_energy_consumption = self.save_customer_energy_consumption()
            load_curve = self.save_load_curve_data()
            customer.to_csv(os.path.join(output_folder,"customer.csv"), index=False)
            billing_cycle.to_csv(os.path.join(output_folder,"billing_cycle.csv"), index=False)
            customer_energy_consumption.to_csv(os.path.join(output_folder,"customer_energy_consumption.csv"), index=False)
            load_curve.to_csv(os.path.join(output_folder,"load_curve.csv"), index=False)
            complete = True     
        except Exception as e:
            print(e)
            complete = False
        finally:
            return complete
    
    
