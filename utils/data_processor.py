import pandas as pd
import json
import numpy as np
from pathlib import Path

class DataProcessor:
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'xlsx', 'xls']
    
    def process_file(self, filepath):
        """Process uploaded file and return pandas DataFrame"""
        file_path = Path(filepath)
        file_extension = file_path.suffix.lower().lstrip('.')
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_extension}")
        
        try:
            if file_extension == 'csv':
                return self._process_csv(filepath)
            elif file_extension == 'json':
                return self._process_json(filepath)
            elif file_extension in ['xlsx', 'xls']:
                return self._process_excel(filepath)
        except Exception as e:
            raise Exception(f"Error processing {file_extension} file: {str(e)}")
    
    def _process_csv(self, filepath):
        """Process CSV file"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(filepath, encoding=encoding)
                return self._clean_dataframe(df)
            except UnicodeDecodeError:
                continue
        
        raise ValueError("Unable to decode CSV file with supported encodings")
    
    def _process_json(self, filepath):
        """Process JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        if isinstance(json_data, list):
            df = pd.DataFrame(json_data)
        elif isinstance(json_data, dict):
            df = pd.DataFrame([json_data])
        else:
            raise ValueError("JSON must contain array of objects or single object")
        
        return self._clean_dataframe(df)
    
    def _process_excel(self, filepath):
        """Process Excel file"""
        df = pd.read_excel(filepath)
        return self._clean_dataframe(df)
    
    def _clean_dataframe(self, df):
        """Clean and prepare DataFrame"""
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        df = df.reset_index(drop=True)
        
        # Clean column names
        df.columns = df.columns.astype(str)
        df.columns = [col.strip().replace(' ', '_') for col in df.columns]
        
        # Handle missing values
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].fillna('Unknown')
            else:
                df[col] = df[col].fillna(0)
        
        return df
    
    def get_column_types(self, df):
        """Analyze column types"""
        column_info = {}
        
        for col in df.columns:
            dtype = str(df[col].dtype)
            unique_count = df[col].nunique()
            null_count = df[col].isnull().sum()
            
            if dtype in ['int64', 'float64']:
                col_type = 'numeric'
            elif dtype == 'object':
                col_type = 'categorical'
            elif 'datetime' in dtype:
                col_type = 'datetime'
            else:
                col_type = 'other'
            
            column_info[col] = {
                'type': col_type,
                'dtype': dtype,
                'unique_values': unique_count,
                'null_values': null_count,
                'sample_values': df[col].head(3).tolist()
            }
        
        return column_info
