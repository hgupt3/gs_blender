import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output  
import numpy as np
from PIL import Image
import os
import base64

def get_renders_dir():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    renders_dir = os.environ.get('GELSIGHT_RENDER_DIR', os.path.join(repo_dir, 'renders'))
    return renders_dir

def list_sensor_dirs(renders_dir):
    entries = os.listdir(renders_dir)
    sensor_dirs = [d for d in entries if d.startswith('sensor_') and os.path.isdir(os.path.join(renders_dir, d))]
    sensor_dirs.sort()
    return sensor_dirs

def get_image_components(sensor_id):
    renders_dir = get_renders_dir()
    sensor_dir = os.path.join(renders_dir, 'sensor_{0:04}'.format(sensor_id), 'samples')
    assert os.path.isdir(sensor_dir), f"Missing sensor samples directory: {sensor_dir}"
    sample_files = [f for f in os.listdir(sensor_dir) if f.endswith('.png')]
    sample_files.sort()
    image_components = []
    for name in sample_files:
        img_path = os.path.join(sensor_dir, name)
        with open(img_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        data_uri = 'data:image/png;base64,' + b64
        image_components.append(html.Img(src=data_uri, style={'height': '100px', 'width': 'auto', 'margin': '2px'}, title=name))
    return image_components

app = Dash(__name__)

app.layout = html.Div([
    html.H2("Sensor Preview",  style={'textAlign': 'center', "font-family": "Arial"}),
    
    html.Div([html.Button('Back', id='back-button', n_clicks=0),
              html.Button('Next', id='next-button', n_clicks=0)],
             style={'textAlign': 'center'}),
    
    html.Br(),
    
    html.Div(id='image-container', style={'display': 'flex', 'flex-wrap': 'wrap', 'justify-content': 'center'}),
    ])

@app.callback(
    Output('image-container', 'children'),
    Input('next-button', 'n_clicks'),
    Input('back-button', 'n_clicks'),
)

def update_graph(next_clicks, back_click):
    renders_dir = get_renders_dir()
    sensors = list_sensor_dirs(renders_dir)
    assert len(sensors) > 0, f"No sensors found in {renders_dir}"
    sensor_id = (next_clicks - back_click) % len(sensors)
    image_components = get_image_components(sensor_id)
    return image_components

if __name__ == '__main__':
    app.run_server(port=8060, debug=True)