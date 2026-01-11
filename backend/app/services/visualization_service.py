import google.generativeai as genai
from app.config import Settings
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from io import BytesIO
import base64
genai.configure(api_key=Settings.GEMINI_API_KEY)

class VisualizationService:
    """Generate visualizations from database data using Gemini"""
    @staticmethod
    def analyze_data_with_gemini(data: dict, query: str) -> dict:
        """
        Ask Gemini to analyze data and suggest best visualization
        
        Args:
            data: Dictionary containing your database data
            query: User's question/request about the data
            
        Returns:
            dict with visualization recommendations
        """
        
        prompt = f"""
        You are a data visualization expert. Analyze this data and suggest the best chart type.

        User Query: {query}

        Data Summary:
        {json.dumps(data, indent=2, default=str)[:2000]}  # Limit to 2000 chars

        Based on this data, respond with ONLY a JSON object (no markdown, no explanation):
        {{
        "chart_type": "line" | "bar" | "pie" | "scatter" | "heatmap",
        "x_axis": "field_name_for_x",
        "y_axis": "field_name_for_y",
        "title": "Suggested chart title",
        "insights": ["insight1", "insight2", "insight3"],
        "color_field": "optional_field_for_color_coding"
        }}
        """
        
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        
        # Clean and parse response
        text = response.text.strip()
        text = text.replace('```json', '').replace('```', '').strip()
        
        return json.loads(text)
    
    @staticmethod
    def generate_attention_over_time_chart(session_data: list) -> str:
        """
        Generate line chart showing attention over time
        
        Args:
            session_data: List of dicts with timestamp and attention metrics
            
        Returns:
            Base64 encoded image string
        """
        df = pd.DataFrame(session_data)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['avg_attention'],
            mode='lines+markers',
            name='Attention Level',
            line=dict(color='#4CAF50', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title='Attention Level Over Time',
            xaxis_title='Time',
            yaxis_title='Attention %',
            yaxis=dict(range=[0, 100]),
            template='plotly_white',
            height=400
        )
        
        # Convert to base64 image
        img_bytes = fig.to_image(format="png")
        img_base64 = base64.b64encode(img_bytes).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    @staticmethod
    def generate_focus_distribution_chart(focused_seconds: int, distracted_seconds: int) -> str:
        """
        Generate pie chart showing focus vs distraction distribution
        """
        fig = go.Figure(data=[go.Pie(
            labels=['Focused', 'Distracted'],
            values=[focused_seconds, distracted_seconds],
            hole=0.4,
            marker=dict(colors=['#4CAF50', '#F44336'])
        )])
        
        fig.update_layout(
            title='Focus Distribution',
            template='plotly_white',
            height=400
        )
        
        img_bytes = fig.to_image(format="png")
        img_base64 = base64.b64encode(img_bytes).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    @staticmethod
    def generate_session_comparison_chart(sessions: list) -> str:
        """
        Generate bar chart comparing multiple sessions
        
        Args:
            sessions: List of dicts with session_id, avg_attention, focused_seconds
        """
        df = pd.DataFrame(sessions)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=df['session_topic'],
            y=df['avg_attention'],
            name='Avg Attention %',
            marker_color='#2196F3'
        ))
        
        fig.update_layout(
            title='Session Performance Comparison',
            xaxis_title='Session',
            yaxis_title='Average Attention %',
            yaxis=dict(range=[0, 100]),
            template='plotly_white',
            height=400
        )
        
        img_bytes = fig.to_image(format="png")
        img_base64 = base64.b64encode(img_bytes).decode()
        
        return f"data:image/png;base64,{img_base64}"

# Singleton instance
visualization_service = VisualizationService()