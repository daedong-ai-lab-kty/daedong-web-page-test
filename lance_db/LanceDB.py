import os
import numpy as np
import pandas as pd
import lancedb

class LanceDB:

    def __init__(self, root_folder_path: str = ''):
        self.db_path = root_folder_path
        print(f'LanceDB path: {self.db_path}')
        self.db = lancedb.connect(self.db_path)
        self.table = None

    def create_or_open_table(self, table_name: str, df: pd.DataFrame = None, overwrite: bool = False):
        
        table_names = self.db.table_names()
        if overwrite and table_name in table_names:
            print(f"Table '{table_name}' already exists. Dropping it.")
            self.db.drop_table(table_name)

        if table_name not in self.db.table_names():
            if df is None:
                raise ValueError("DataFrame must be provided to create a new table.")
            print(f"Creating new table: {table_name}")
            self.table = self.db.create_table(table_name, data=df)
        else:
            print(f"Opening existing table: {table_name}")
            self.table = self.db.open_table(table_name)
        
        return self.table

    def create_index(self, num_partitions: int = 256, num_sub_vectors: int = 96):

        if self.table is None:
            raise ValueError("Table is not opened or created yet.")

        print("\n--- Creating IVF_PQ Index ---")
        # create_index는 데이터가 이미 있는 테이블에 후속으로 생성하는 경우 사용
        self.table.create_index(
            metric="cosine", # or L2
            num_partitions=num_partitions,
            num_sub_vectors=num_sub_vectors
        )
        print("Index created successfully.")

    def filter_sql(self,
               filter: str = None,
               nprobes: int = 10):

        if self.table is None:
            raise ValueError("Table is not opened or created yet. Call create_or_open_table() first.")
        
        query_builder = self.table.search()

        print(f"Applying SQL filter: {filter}")
        query = query_builder.where(filter)
            
        result_df = query.to_df()
        
        return result_df

    def search(self,
               query_vector: np.ndarray,
               top_k: int = 5,
               prefilter: str = None,
               nprobes: int = 10):

        if self.table is None:
            raise ValueError("Table is not opened or created yet. Call create_or_open_table() first.")
            
        query = self.table.search(query_vector).limit(top_k)

        if prefilter:
            print(f"Applying pre-filter: {prefilter}")
            query = query.where(prefilter)
        
        # 인덱스가 있는 경우 nprobes 설정
        # lancedb는 자동으로 인덱스 존재 여부를 확인
        query = query.nprobes(nprobes)
            
        result_df = query.to_df()
        
        return result_df

    def export_to_parquet(self, table_name: str, output_path: str):

        print(f"'{table_name}' exports Parquet file...")
        
        if self.table is None:
            raise ValueError("Table is not opened or created yet.")
        
        table_to_export = self.db.open_table(table_name)

        df = table_to_export.to_pandas()

        try:
            df.to_parquet(output_path, index=False)
            print(f"Save {output_path}")
        except Exception as e:
            print(f"ERROR: {e}")