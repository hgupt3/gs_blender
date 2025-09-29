import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output  
import numpy as np
from PIL import Image
import os
import base64

app = Dash(__name__)

def get_renders_dir():
    repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    renders_dir = os.environ.get('GELSIGHT_RENDER_DIR', os.path.join(repo_dir, 'renders'))
    return renders_dir

def list_sensor_dirs(renders_dir):
    entries = os.listdir(renders_dir)
    sensor_dirs = [d for d in entries if d.startswith('sensor_') and os.path.isdir(os.path.join(renders_dir, d))]
    sensor_dirs.sort()
    return sensor_dirs

def get_image_components(render_idx):
    renders_dir = get_renders_dir()
    sensor_dirs = list_sensor_dirs(renders_dir)
    # Fail fast if no sensors
    assert len(sensor_dirs) > 0, f"No sensors found in {renders_dir}"
    image_components = []
    for sensor in sensor_dirs:
        img_path = os.path.join(renders_dir, sensor, 'samples', '{0:04}.png'.format(render_idx))
        assert os.path.exists(img_path), f"Missing sample image: {img_path}"
        with open(img_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        data_uri = 'data:image/png;base64,' + b64
        image_components.append(html.Img(src=data_uri, style={'height': '200px', 'width': 'auto', 'margin': '3px'}, title=sensor))
    return image_components

app.layout = html.Div([
    html.H2("Render Preview",  style={'textAlign': 'center', "font-family": "Arial"}),
    
    dcc.Graph(id='dmap', figure={}),    
    
    html.Div([html.Button('Back', id='prev', n_clicks=0,),
              html.Button('Next', id='next', n_clicks=0),], 
             style={'textAlign': 'center'}),
    
    html.Br(),
    
    html.Div(id='image-container', style={'display': 'flex', 'flex-wrap': 'wrap', 'justify-content': 'center'}),
])

@app.callback(
    Output('dmap', 'figure'),
    Output('image-container', 'children'),
    Input('next', 'n_clicks'), 
    Input('prev', 'n_clicks'),
)

def update_graph(next_clicks, back_click):
    renders_dir = get_renders_dir()
    sensor_dirs = list_sensor_dirs(renders_dir)
    assert len(sensor_dirs) > 0, f"No sensors found in {renders_dir}"
    first_sensor = sensor_dirs[0]
    samples_dir = os.path.join(renders_dir, first_sensor, 'samples')
    sample_files = [f for f in os.listdir(samples_dir) if f.endswith('.png')]
    sample_files.sort()
    assert len(sample_files) > 0, f"No samples found in {samples_dir}"
    render_idx = (next_clicks - back_click) % len(sample_files)

    dmap_path = os.path.join(renders_dir, first_sensor, 'raw_data', '{0:04}.npy'.format(render_idx))
    dmap = np.load(dmap_path)
    xs = []
    ys = []
    zs = []
    height, width = dmap.shape
    for y in range(height):
        for x in range(width):
            xs.append(width - x)
            ys.append(y)
            if dmap[y][x] < 0: dmap[y][x] = 0
            zs.append(dmap[y][x] * 5)

    fig = go.Figure(data=[go.Scatter3d(x=xs, 
                                       y=ys, 
                                       z=zs, 
                                       mode='markers', 
                                       marker=dict(size=1.5,
                                                   cmax=3,
                                                   cmin=0, 
                                                   color=zs, 
                                                   colorscale='Viridis', 
                                                   opacity=1.0))])
    
    fig.update_layout(scene = dict(xaxis = dict(tickmode="array", tickvals=[], range=[0,width], backgroundcolor="rgba(0, 0, 0, 0)", title=dict(text="")),
                                   yaxis = dict(tickmode="array", tickvals=[], range=[0,height], backgroundcolor="rgba(0, 0, 0, 0)", title=dict(text="")),
                                   zaxis = dict(tickmode="array", tickvals=[], range=[0,5], backgroundcolor="rgba(0, 0, 0, 0)", title=dict(text="")),
                                   
                                   aspectmode='manual', 
                                   aspectratio=dict(x=1, y=1, z=0.25),
                                   camera = dict(eye=dict(x=0, y=0, z=1.2), 
                                                 up=dict(x=0, y=0, z=0))),
                      margin=dict(l=0, r=0, b=0, t=0),)

    image_components = get_image_components(render_idx)
    return fig, image_components

if __name__ == '__main__':
    app.run_server(debug=True)