from .consumer_meter import ConsumerMeter
from sqlalchemy import text, bindparam
import pandas as pd


class ServiceDropWires(ConsumerMeter):
    def __init__(self, substation_id, billing_period, db_engine):
        super().__init__(substation_id, billing_period, db_engine)
        self.customer_ids = self.save_customer_data()['customer_id'].tolist()

    def getservice_drop(self):
        stmt = text("""
        SELECT *
        FROM gis.service_drop AS sd
        JOIN gis.conductor_wires AS cw
            ON sd.conductor_type = cw.id
        WHERE sd.to_customer_id IN :customer_id
    """).bindparams(
            bindparam("customer_id", expanding=True)
        )

        df = pd.read_sql(
            stmt,
            self.db_engine,
            params={"customer_id": self.customer_ids}
        )
        df['installation_type'] = 1
        return df

    def secondary_service_drop(self):
        sd = self.getservice_drop()
        sd = sd.loc[sd['description'].str.contains(
            r"SECONDARY", case=False, regex=True)]
        sd = sd[['service_drop_id', 'from_bus_id', 'to_customer_id',
                 'phasing', 'installation_type', 'length_meters_1', 'length_meters_2',
                 'type', 'size', 'unit', 'strand']]
        sd.insert(0, "count", sd.index + 1)
        return sd

    def primary_service_drop(self):
        try:
            pl = self.process_primary_lines()
            pl.drop(columns=['phasing'], inplace=True)
            psd = self.getservice_drop()
            psd = psd.loc[psd['description'].str.contains(
                r"PRIMARY", case=False, regex=True
            )]
            psd = psd[['service_drop_id', 'from_bus_id', 'to_customer_id',
                       'phasing','length_meters_1', 'type', 'size', 'unit', 'strand',]]
            psd = psd.merge(pl, how="left", left_on="from_bus_id",
                            right_on="to_bus_id")
            psd = psd[['service_drop_id', 'from_bus_id_x', 'to_customer_id', 'phasing', 
                       'configuration','system_ground_type', 'length_meters_1','type',
                       'size', 'unit', 'strand',  'neutral_type', 'neutral_size',
                       'neutral_unit', 'neutral_strand','spacing_d12_meters', 'spacing_d23_meters',
                       'spacing_d13_meters', 'spacing_d1n_meters', 'spacing_d2n_meters',
                       'spacing_d3n_meters', 'spacing_dc1_c2_meters', 'height_h1_meters',
                       'height_h2_meters', 'height_h3_meters', 'height_hn_meters',
                       'earth_resistivity_ohm_meter']]
            return psd
        except Exception as e:
            print(e)
