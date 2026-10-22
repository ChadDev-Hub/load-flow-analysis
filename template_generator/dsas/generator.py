import pandas as pd
import geopandas as gpd
from sqlalchemy import text, create_engine, bindparam, Engine
from dotenv import load_dotenv
from datetime import datetime



pd.options.display.float_format = '{:,.2f}'.format
pd.options.display.max_columns = None
import calendar


class DSAS_TEMPLATE_GENERATOR:
    def __init__(self, substation_id, billing_period, db_engine:Engine):
        self.substation_id = substation_id
        self.billing_period = billing_period
        self.year = billing_period[:4]
        self.db_engine = db_engine
        
    # READ AND PROCESS DATABASE DATA
    # CONSUMER METER
    def read_and_process_consumer_meter(self):
            # QUERY CONSUMER METER DATA FROM DATA BASE
            stmt = text("""
                        select cm.*, b.substation_id, b.nominal_voltage_kv, sd.phasing from gis.consumer_meter as cm
                        join gis.service_drop as sd
                        on cm.account_no = sd.to_customer_id
                        join gis.bus as b
                        on b.bus_id = sd.from_bus_id
                        where b.substation_id IN :substation
                        """).bindparams(
                bindparam("substation", expanding=True)
            )
            cm_df = gpd.read_postgis(stmt, self.db_engine, geom_col='geom', params={"substation": self.substation_id})
    
            # LUMP DATA
            lump_cm_df = cm_df[cm_df['account_type'] == 'Consumer Lump']
            lump_cm_df.sort_values(by='account_no', inplace=True)
            
            
            
            kwh_df = pd.read_csv(f"converted_kwr/{self.year}/{self.billing_period}.csv")
            kwh_df['account_no'] = kwh_df['account_no'].str.replace("-", "", regex=False).str.strip().astype("string")
            kwh_df.kwh_used = kwh_df.kwh_used.apply(lambda x: x.replace(",", "")).astype("float")
            kwh_df.previous_reading = kwh_df.previous_reading.apply(lambda x: x.replace(",", "")).astype("float")
            kwh_df.present_reading = kwh_df.present_reading.apply(lambda x: x.replace(",", "")).astype("float")
            # KWH DATA WITH GEOMETRY
            kwh_df_with_geom = kwh_df.merge(cm_df, how="inner", left_on="account_no", right_on="account_no")
            kwh_df_with_geom = kwh_df_with_geom[['account_no', 'account_name', 'kwh_used', 'account_type', 'substation_id', 'nominal_voltage_kv', 'phasing' ]]
            kwh_df_with_geom.rename(columns={
                'account_no' : 'customer_id',
                'account_name': 'customer_name',
                'account_type' : 'customer_type',   
            },inplace=True)
            
            kwh_df_with_geom['customer_id'].apply(lambda x: x[:6] + "0000").unique()
                    # KWH LUMP DATA
            kwh_df_without_geom = kwh_df.loc[~kwh_df['account_no'].isin(kwh_df_with_geom['customer_id'])]
            kwh_df_without_geom['lump_account_no'] = kwh_df_without_geom['account_no'].apply(lambda x: x[:6] + "0000")
            lump_kwh_filter = lump_cm_df.merge(kwh_df_without_geom, how="inner", left_on="account_no", right_on="lump_account_no")
            lump_kwh_filter = lump_kwh_filter.groupby(["lump_account_no", "account_name", "account_type",'substation_id', 'nominal_voltage_kv', 'phasing']).agg({
                "kwh_used" : "sum"
            }).reset_index()
            
            
            lump_kwh_filter.rename(columns={
                'lump_account_no' : 'customer_id',
                'account_name' : 'customer_name',
                'account_type' : 'customer_type'
            },inplace=True)
            clean_kwh_df = pd.concat([kwh_df_with_geom, lump_kwh_filter])
            
            
    
            
            # MFSR DATA
            mfsr_data = pd.read_csv(f"mfsr/cleaned/mfsr_{self.year}.csv")
            mfsr_data = mfsr_data[['substation_id','Sales in KWH', 'billing_period']]
            mfsr_data = mfsr_data.loc[mfsr_data['billing_period'].astype(str) == str(self.billing_period)]
            mfsr_data = mfsr_data.loc[mfsr_data['substation_id'].astype(str).isin(self.substation_id)]
            
            
            
            # SCALING KWH DATA
            scaled_kwh_df = clean_kwh_df.copy()
            kwh_diff = mfsr_data.copy()
            kwh_sales = mfsr_data['Sales in KWH'].sum()
            kwh_used = scaled_kwh_df['kwh_used'].sum()
            kwh_diff['difference'] = kwh_sales / kwh_used
            kwh_diff = kwh_diff[['substation_id', 'difference', 'billing_period']]
            
            
            scaled_kwh_df = scaled_kwh_df.merge(kwh_diff, how="left", left_on="substation_id", right_on="substation_id")
            scaled_kwh_df[
                'scaled_kwh_used'] = scaled_kwh_df['kwh_used'] * scaled_kwh_df['difference']
            scaled_kwh_df[
                'kwh_used'
            ] = scaled_kwh_df['scaled_kwh_used']
            scaled_kwh_df.drop(columns=['difference', 'scaled_kwh_used'], inplace=True)
            return scaled_kwh_df
    # BUS
    def process_bus_data(self):
        stmt = text("""
            select * from gis.bus
            where substation_id in :substation
            """).bindparams(bindparam("substation", expanding=True))
        bus_df = gpd.read_postgis(stmt, self.db_engine, geom_col='geom', params={"substation": self.substation_id})
        bus_df = bus_df[['bus_id','description','nominal_voltage_kv', 'geom']]
        return bus_df
    # PRIMARY LINE OVERHEAD
    def process_primary_lines(self):
        stmt = text('''
            select pl.*, b.feeder_id,
            cw.type as conductor_type,
            cw.size as conductor_size,
            cw.unit as conductor_unit,
            cw.strand as conductor_strand,
            nc.type as neutral_type,
            nc.size as neutral_size,
            nc.unit as neutral_unit,
            nc.strand as neutral_strand
            from gis.primary_lines as pl
            left join gis.bus as b
            on b.bus_id = pl.from_bus_id
            left join gis.conductor_wires as cw
            on cw.id = pl.conductor_wire
            left join gis.neutral_concentric_cable as nc
            on pl.neutral_wire = nc.id
            where b.substation_id in :substation
            ''').bindparams(bindparam("substation", expanding=True))
        
        pl_df = gpd.read_postgis(stmt, self.db_engine, geom_col="geom", params={
            "substation": self.substation_id})
        pl_spacing = pd.read_excel(r"sample-data\cor_bus_202401.xls", sheet_name="Primary Line-Overhead", engine="calamine")
        spacing_data = pl_spacing.iloc[:, list(range(4, 6)) + list(range(16, pl_spacing.shape[1]))].columns
        pl_spacing = pl_spacing[spacing_data]
        pl_spacing.drop_duplicates(subset=['Phasing', 'Configuration'], inplace=True)
        pl_spacing.columns = pl_spacing.columns.str.replace(r"\(|\)", "", regex=True)
        pl_spacing.columns = pl_spacing.columns.str.replace(r"\s+|-+", "_", regex=True).str.lower()
        pl_spacing['configuration'] = pl_spacing['configuration'].str.upper()
        pl_df = pl_df.merge(pl_spacing, how="left", left_on=["phasing","configuration"], right_on=["phasing","configuration"])
        return pl_df
    
    
    # DISTRIBUTION TRANSFORMER
    def process_distribution_transformer(self):
        stmt = text(
            """
            select dt.*, tt.kva_rating, tt.primary_voltage_rating, secondary_voltage_rating from gis.distribution_transformer as dt 
            left join gis.bus as b
            on  b.bus_id = dt.from_primary_bus_id
            left join gis.transformer_type as tt 
            on tt.id = dt.transformer_type
            where b.substation_id in :substation
            
            """
        ).bindparams(bindparam("substation", expanding=True))
        dt_df = gpd.read_postgis(stmt, self.db_engine, geom_col='geom', params={"substation":self.substation_id})


        cor_bus_dt_df = pd.read_excel("./sample-data/cor_bus_202401.xls", sheet_name="Distribution Transformer", engine="calamine")
        unique_values_df = cor_bus_dt_df[
                [
                    'KVA Rating',
                    'Secondary Voltage Rating (kV)',
                    'Primary Voltage Rating(kV)',
                    'X/R Ratio',
                    'No-Load Loss (kW)',
                    'Exciting Current (%)'
                ]
            ]

        unique_values_df = unique_values_df.drop_duplicates()
        dt_df['kva_rating'] = dt_df['kva_rating'].apply(lambda x: x.replace("kVA", "")).astype("float")
        dt_merge = dt_df.merge(unique_values_df, how="left", 
                    left_on=["kva_rating", 'primary_voltage_rating', 'secondary_voltage_rating'], 
                    right_on=["KVA Rating", 'Primary Voltage Rating(kV)', 'Secondary Voltage Rating (kV)'])
        dt_merge.drop(columns=['Primary Voltage Rating(kV)', 'Secondary Voltage Rating (kV)','remarks','image','is_active'], inplace=True)
        dt_clean = dt_merge
        return dt_clean
    
    # PROCESS SECONDARY LINES
    
    def read_process_secondary_lines(self):
        try:
            stmt = text(
                """select sl.*,cw.* from gis.secondary_lines as sl
                join gis.bus as b
                on b.bus_id = sl.from_bus_id
                join gis.conductor_wires as cw
                on cw.id = sl.conductor_type
                where b.substation_id in :substation
                """
            ).bindparams(bindparam("substation", expanding=True))
            sl_df = pd.read_sql(stmt, self.db_engine, params={"substation": self.substation_id})
            return sl_df
        except Exception as e:
            raise e