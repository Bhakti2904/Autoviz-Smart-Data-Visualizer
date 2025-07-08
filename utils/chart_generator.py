import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

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
