import pandas as pd
import json
from io import StringIO, BytesIO
import tempfile

class ExportHandler:
    def export_as_csv(self, df):
        """Export DataFrame as CSV"""
        output = StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        # Convert to BytesIO for Flask send_file
        csv_bytes = BytesIO()
        csv_bytes.write(output.getvalue().encode('utf-8'))
        csv_bytes.seek(0)
        
        return csv_bytes
    
    def export_as_json(self, df):
        """Export DataFrame as JSON"""
        json_str = df.to_json(orient='records', indent=2)
        
        json_bytes = BytesIO()
        json_bytes.write(json_str.encode('utf-8'))
        json_bytes.seek(0)
        
        return json_bytes
    
    def export_chart_config(self, config):
        """Export chart configuration"""
        config_str = json.dumps(config, indent=2)
        
        config_bytes = BytesIO()
        config_bytes.write(config_str.encode('utf-8'))
        config_bytes.seek(0)
        
        return config_bytes
