from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
import json
import os
from werkzeug.utils import secure_filename
import tempfile
from io import BytesIO
import numpy as np
from flask import Flask

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'autoviz-secret-key-2024'

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Store data in memory (in production, use Redis or database)
app_data = {
    'current_data': None,
    'current_headers': None,
    'chart_config': {}
}

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif pd.isna(obj):
        return None
    return obj

def clean_data_for_json(data):
    """Clean data structure for JSON serialization"""
    if isinstance(data, list):
        return [clean_data_for_json(item) for item in data]
    elif isinstance(data, dict):
        return {key: clean_data_for_json(value) for key, value in data.items()}
    else:
        return convert_numpy_types(data)

class DataProcessor:
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'xlsx', 'xls']
    
    def process_file(self, file):
        """Process uploaded file and return pandas DataFrame"""
        filename = file.filename.lower()
        
        try:
            if filename.endswith('.csv'):
                return self._process_csv(file)
            elif filename.endswith('.json'):
                return self._process_json(file)
            elif filename.endswith(('.xlsx', '.xls')):
                return self._process_excel(file)
            else:
                raise ValueError(f"Unsupported file format")
        except Exception as e:
            raise Exception(f"Error processing file: {str(e)}")
    
    def _process_csv(self, file):
        """Process CSV file"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                file.seek(0)
                df = pd.read_csv(file, encoding=encoding)
                return self._clean_dataframe(df)
            except (UnicodeDecodeError, pd.errors.EmptyDataError):
                continue
        
        raise ValueError("Unable to decode CSV file")
    
    def _process_json(self, file):
        """Process JSON file"""
        try:
            file.seek(0)
            json_data = json.load(file)
            
            if isinstance(json_data, list):
                df = pd.DataFrame(json_data)
            elif isinstance(json_data, dict):
                df = pd.DataFrame([json_data])
            else:
                raise ValueError("JSON must contain array of objects or single object")
            
            return self._clean_dataframe(df)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON format: {str(e)}")
    
    def _process_excel(self, file):
        """Process Excel file"""
        try:
            file.seek(0)
            df = pd.read_excel(file)
            return self._clean_dataframe(df)
        except Exception as e:
            raise Exception(f"Excel processing error: {str(e)}")
    
    def _clean_dataframe(self, df):
        """Clean and prepare DataFrame"""
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        df = df.reset_index(drop=True)
        
        # Clean column names
        df.columns = df.columns.astype(str)
        df.columns = [col.strip().replace(' ', '_').replace('.', '_') for col in df.columns]
        
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
            unique_count = int(df[col].nunique())  # Convert to int
            null_count = int(df[col].isnull().sum())  # Convert to int
            
            if dtype in ['int64', 'float64', 'int32', 'float32']:
                col_type = 'numeric'
            elif dtype == 'object':
                col_type = 'categorical'
            elif 'datetime' in dtype:
                col_type = 'datetime'
            else:
                col_type = 'other'
            
            # Convert sample values to native Python types
            sample_values = [convert_numpy_types(val) for val in df[col].head(3).tolist()]
            
            column_info[col] = {
                'type': col_type,
                'dtype': dtype,
                'unique_values': unique_count,
                'null_values': null_count,
                'sample_values': sample_values
            }
        
        return column_info

class ChartGenerator:
    def __init__(self):
        self.color_palettes = {
            'default': px.colors.qualitative.Plotly,
            'viridis': px.colors.sequential.Viridis,
            'plasma': px.colors.sequential.Plasma,
            'blues': px.colors.sequential.Blues,
            'reds': px.colors.sequential.Reds,
            'greens': px.colors.sequential.Greens,
            'sunset': px.colors.sequential.Sunset,
            'ocean': px.colors.sequential.Teal,
            'purple': px.colors.sequential.Purples
        }
    
    def create_chart(self, df, config):
        """Create chart based on configuration"""
        chart_type = config.get('chart_type', 'bar')
        x_axis = config.get('x_axis')
        y_axis = config.get('y_axis')
        color_scheme = config.get('color_scheme', 'default')
        title = config.get('title', 'Data Visualization')
        
        try:
            if chart_type == 'bar':
                return self._create_bar_chart(df, x_axis, y_axis, color_scheme, title)
            elif chart_type == 'line':
                return self._create_line_chart(df, x_axis, y_axis, color_scheme, title)
            elif chart_type == 'scatter':
                return self._create_scatter_chart(df, x_axis, y_axis, color_scheme, title)
            elif chart_type == 'pie':
                return self._create_pie_chart(df, x_axis, y_axis, color_scheme, title)
            elif chart_type == 'area':
                return self._create_area_chart(df, x_axis, y_axis, color_scheme, title)
            elif chart_type == 'histogram':
                return self._create_histogram(df, x_axis, color_scheme, title)
            elif chart_type == 'box':
                return self._create_box_plot(df, x_axis, y_axis, color_scheme, title)
            elif chart_type == 'heatmap':
                return self._create_heatmap(df, color_scheme, title)
            else:
                return None
        except Exception as e:
            print(f"Error creating chart: {str(e)}")
            return None
    
    def _create_bar_chart(self, df, x_axis, y_axis, color_scheme, title):
        fig = px.bar(df, x=x_axis, y=y_axis, title=title,
                    color_discrete_sequence=self.color_palettes.get(color_scheme))
        return self._style_chart(fig)
    
    def _create_line_chart(self, df, x_axis, y_axis, color_scheme, title):
        fig = px.line(df, x=x_axis, y=y_axis, title=title,
                     color_discrete_sequence=self.color_palettes.get(color_scheme))
        return self._style_chart(fig)
    
    def _create_scatter_chart(self, df, x_axis, y_axis, color_scheme, title):
        fig = px.scatter(df, x=x_axis, y=y_axis, title=title,
                        color_discrete_sequence=self.color_palettes.get(color_scheme))
        return self._style_chart(fig)
    
    def _create_pie_chart(self, df, names_col, values_col, color_scheme, title):
        if values_col and values_col in df.columns:
            pie_data = df.groupby(names_col)[values_col].sum().reset_index()
        else:
            pie_data = df[names_col].value_counts().reset_index()
            pie_data.columns = [names_col, 'count']
            values_col = 'count'
        
        fig = px.pie(pie_data, names=names_col, values=values_col, title=title,
                    color_discrete_sequence=self.color_palettes.get(color_scheme))
        return self._style_chart(fig)
    
    def _create_area_chart(self, df, x_axis, y_axis, color_scheme, title):
        fig = px.area(df, x=x_axis, y=y_axis, title=title,
                     color_discrete_sequence=self.color_palettes.get(color_scheme))
        return self._style_chart(fig)
    
    def _create_histogram(self, df, x_axis, color_scheme, title):
        fig = px.histogram(df, x=x_axis, title=title,
                          color_discrete_sequence=self.color_palettes.get(color_scheme))
        return self._style_chart(fig)
    
    def _create_box_plot(self, df, x_axis, y_axis, color_scheme, title):
        if y_axis and y_axis in df.columns:
            fig = px.box(df, x=x_axis, y=y_axis, title=title,
                        color_discrete_sequence=self.color_palettes.get(color_scheme))
        else:
            fig = px.box(df, y=x_axis, title=title,
                        color_discrete_sequence=self.color_palettes.get(color_scheme))
        return self._style_chart(fig)
    
    def _create_heatmap(self, df, color_scheme, title):
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty:
            return None
        
        corr_matrix = numeric_df.corr()
        fig = px.imshow(corr_matrix, title=title, 
                       color_continuous_scale=color_scheme, aspect="auto")
        return self._style_chart(fig)
    
    def _style_chart(self, fig):
        """Apply consistent styling"""
        fig.update_layout(
            font_family="Inter, system-ui, sans-serif",
            font_size=14,
            title_font_size=20,
            title_font_color="#1f2937",
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=60, r=60, t=80, b=60),
            height=500,
            title_x=0.5
        )
        
        fig.update_xaxes(
            showgrid=True, gridwidth=1, gridcolor="#f1f5f9",
            showline=True, linewidth=2, linecolor="#e5e7eb"
        )
        
        fig.update_yaxes(
            showgrid=True, gridwidth=1, gridcolor="#f1f5f9",
            showline=True, linewidth=2, linecolor="#e5e7eb"
        )
        
        return fig

class ExportHandler:
    def export_as_csv(self, df):
        """Export DataFrame as CSV"""
        output = BytesIO()
        csv_data = df.to_csv(index=False)
        output.write(csv_data.encode('utf-8'))
        output.seek(0)
        return output
    
    def export_as_json(self, df):
        """Export DataFrame as JSON"""
        # Convert DataFrame to dict and clean for JSON serialization
        data_dict = df.to_dict('records')
        cleaned_data = clean_data_for_json(data_dict)
        json_str = json.dumps(cleaned_data, indent=2)
        
        output = BytesIO()
        output.write(json_str.encode('utf-8'))
        output.seek(0)
        return output

# Initialize processors
data_processor = DataProcessor()
chart_generator = ChartGenerator()
export_handler = ExportHandler()

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file:
            # Process the file directly from memory
            df = data_processor.process_file(file)
            
            # Convert DataFrame to dict and clean for JSON serialization
            data_records = df.to_dict('records')
            cleaned_data = clean_data_for_json(data_records)
            
            # Store data
            app_data['current_data'] = cleaned_data
            app_data['current_headers'] = df.columns.tolist()
            
            # Get column info
            column_info = data_processor.get_column_types(df)
            
            return jsonify({
                'success': True,
                'data': cleaned_data[:100],  # Send first 100 rows
                'headers': app_data['current_headers'],
                'total_rows': len(cleaned_data),
                'column_info': column_info
            })
    
    except Exception as e:
        print(f"Upload error: {str(e)}")  # Debug logging
        return jsonify({'error': str(e)}), 500

@app.route('/generate_chart', methods=['POST'])
def generate_chart():
    """Generate chart based on configuration"""
    try:
        config = request.json
        
        if not app_data['current_data']:
            return jsonify({'error': 'No data available'}), 400
        
        # Convert data back to DataFrame
        df = pd.DataFrame(app_data['current_data'])
        
        # Generate chart
        fig = chart_generator.create_chart(df, config)
        
        if fig is None:
            return jsonify({'error': 'Unable to generate chart'}), 400
        
        # Convert to JSON for frontend
        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
        # Store config
        app_data['chart_config'] = config
        
        return jsonify({
            'success': True,
            'chart': chart_json,
            'config': config
        })
    
    except Exception as e:
        print(f"Chart generation error: {str(e)}")  # Debug logging
        return jsonify({'error': str(e)}), 500

@app.route('/export_data/<format>')
def export_data(format):
    """Export data in specified format"""
    try:
        if not app_data['current_data']:
            return jsonify({'error': 'No data available'}), 400
        
        df = pd.DataFrame(app_data['current_data'])
        
        if format == 'csv':
            output = export_handler.export_as_csv(df)
            return send_file(
                output,
                as_attachment=True,
                download_name='autoviz_data.csv',
                mimetype='text/csv'
            )
        
        elif format == 'json':
            output = export_handler.export_as_json(df)
            return send_file(
                output,
                as_attachment=True,
                download_name='autoviz_data.json',
                mimetype='application/json'
            )
        
        else:
            return jsonify({'error': 'Unsupported format'}), 400
    
    except Exception as e:
        print(f"Export error: {str(e)}")  # Debug logging
        return jsonify({'error': str(e)}), 500

@app.route('/get_data_stats')
def get_data_stats():
    """Get data statistics"""
    try:
        if not app_data['current_data']:
            return jsonify({'error': 'No data available'}), 400
        
        df = pd.DataFrame(app_data['current_data'])
        
        stats = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'numeric_columns': len(df.select_dtypes(include=['number']).columns),
            'categorical_columns': len(df.select_dtypes(include=['object']).columns),
            'missing_values': int(df.isnull().sum().sum()),
            'memory_usage': int(df.memory_usage(deep=True).sum())
        }
        
        return jsonify(stats)
    
    except Exception as e:
        print(f"Stats error: {str(e)}")  # Debug logging
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
