import dash
from dash import dcc, html, Output, Input, State, callback_context, ALL, MATCH
import dash_mantine_components as dmc
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

from ising_sim import IsingSim

models = {
    'Ferromagnet': IsingSim(N=20),
    'Election':     IsingSim(N=20),
    'Stock Market': IsingSim(N=20)
}

color_maps = {
    'Ferromagnet': ["#9aa2a6", "#515d63"],   # Light Gray/Dark Gray
    'Election': ["#457b9d", "#e63946"],   # Blue/Red
    'Stock Market': ["#00C853", "#D50000"]    # Green/Red
}

character_maps = {
    'Ferromagnet': {1: '+', -1: '–'},
    'Election':    {1: 'D', -1: 'R'},
    'Stock Market':{1: 'B', -1: 'S'}
}

event_options = {
    'Ferromagnet': [
        {'label': 'Positive Electric Field', 'value': 'positive_field'},
        {'label': 'Negative Electric Field', 'value': 'negative_field'},
        {'label': 'Oscillating Field',       'value': 'oscillate_field'},
    ],
    'Election': [
        {'label': 'Healthcare Expansion', 'value': 'pro_d'},
        {'label': 'Tax Cut', 'value': 'pro_r'},
        {'label': 'Climate Agreement Passed', 'value': 'con_r'},
        {'label': 'Corporate Deregulation Passed', 'value': 'con_d'},
    ],
    'Stock Market': [
        {'label': 'Positive Earnings',   'value': 'positive_earnings'},
        {'label': 'Negative Earnings',   'value': 'negative_earnings'},
        {'label': 'Interest Rate Hike',  'value': 'rate_hike'},
        {'label': 'Interest Rate Cut',   'value': 'rate_cut'}
    ]
}

event_mapping = {
    'positive_field': 0.3,
    'negative_field': -0.3,
    'oscillate_field': np.random.choice([0.3, -0.3]),
    'pro_d': 0.5,
    'pro_r': -0.5,
    'con_r': 0.3,
    'con_d': -0.3,
    'positive_earnings': 0.3,
    'negative_earnings': -0.3,
    'rate_hike': 1.0,
    'rate_cut': -1.0
}

spin_distribution_titles = {
    'Ferromagnet': '   Distribution by Magnetic Domain',
    'Election':    '   Distribution by Demographic Group',
    'Stock Market':'   Distribution by Market Participant'
}

gauge_titles = {
    'Ferromagnet': "Magnetization   ",
    'Election': "Partisan Tilt   ",
    'Stock Market': "Market Sentiment   "
}

agreement_titles = {
    'Ferromagnet':      ("Local Magnetic Alignment   ", "Misaligned", "Alignment"),
    'Election':         ("Local Voter Consensus   ",    "Polarized", "Consensus"),
    'Stock Market':     ("Local Market Herding   ",     "Diverging",  "Herding")
}

glow_layers = [
    {"size": 14, "opacity": 0.08},
    {"size": 10, "opacity": 0.12},
    {"size": 7,  "opacity": 0.25},
    {"size": 5,  "opacity": 0.4},
    {"size": 3,  "opacity": 0.65},
]

blue = "0, 191, 255"

black = "rgb(18, 18, 18)"

white = "rgb(229, 229, 229)"

def compute_faction_borders(faction_map):
    N = faction_map.shape[0]
    x_points = []
    y_points = []
    for r in range(N):
        for c in range(N):
            curr = faction_map[r, c]
            for dr, dc in [(0, 1), (1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N:
                    neighbor = faction_map[nr, nc]
                    if curr != neighbor:
                        epsilon = 0.06
                        offset = 0.5
                        if dr == 1:  # bottom neighbor (drawing a horizontal border)
                            if 0 < c < N-1:  # check columns for horizontal borders
                                x0, x1 = c - epsilon - offset, c + 1 + epsilon - offset
                            else:  # touching left/right edge
                                x0, x1 = c - offset, c + 1 - offset
                            y0 = y1 = r + 1 - offset
                            x_points += [x0, x1, None]
                            y_points += [y0, y1, None]
                        else:  # right neighbor (drawing a vertical border)
                            if 0 < r < N-1:  # check rows for vertical borders
                                y0, y1 = r - epsilon - offset, r + 1 + epsilon - offset
                            else:  # touching top/bottom edge
                                y0, y1 = r - offset, r + 1 - offset
                            x0 = x1 = c + 1 - offset
                            x_points += [x0, x1, None]
                            y_points += [y0, y1, None]

    return x_points, y_points

def compute_faction_labels(faction_map):
    labels = []
    unique_factions = np.unique(faction_map)
    for f_id in unique_factions:
        ys, xs = np.where(faction_map == f_id)
        if len(xs) > 0:
            center_x = np.mean(xs)
            center_y = np.mean(ys)
            labels.append((center_x, center_y, int(f_id)+1))  # +1 to label 1-indexed
    return labels

def create_faction_h_sliders(sim):
    sliders = []

    for i, h in enumerate(sim.h_values):
        sliders.append(
            html.Div([
                html.Span(f"Group {i+1} Bias (h)", title="How much group {i+1} favors +1 vs. -1"),
                dmc.Slider(
                    id={'type': 'faction-h-slider', 'index': i},
                    min=-2,
                    max=2,
                    step=0.05,
                    value=h,
                    marks=[{"value": v, "label": str(v)} for v in [-2, -1, 0, 1, 2]],
                    color="blue",
                    size="lg",
                    style={'marginBottom': '25px'}
                )
            ])
        )
    return sliders

initial_store = {}
for name, sim in models.items():
    state = sim.get_current_state()
    faction_map = np.array(state['faction_map'])

    borders_x, borders_y = compute_faction_borders(faction_map)
    labels = compute_faction_labels(faction_map)

    initial_store[name] = {
        'lattice':        state['lattice'].tolist(),
        'energies':       state['energies'].tolist(),
        'faction_map':    state['faction_map'].tolist(),
        'borders_x': borders_x,
        'borders_y': borders_y,
        'labels':         labels,
        'constants': {
            'J_intra': sim.J_intra,
            'J_inter': sim.J_inter,
            'T':       sim.T
        },
        'snapshots':      [],
        'current_trial':  state['current_trial'],
        'active':         (name == 'Ferromagnet')
    }

app = dash.Dash(
    __name__, 
    external_stylesheets=[
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap'
    ]
)
server = app.server

tab_style = {
    'alignItems': 'top',
    'justifyContent': 'center',
    'fontSize': '17px',
    'fontWeight': '500',
    'textTransform': 'uppercase',
    'letterSpacing': '1px',
    'padding': '10px 0',
    'flex': 1
}

app.layout = dmc.MantineProvider(
    theme={"colorScheme": "dark"},
    children=[
        html.Div(style={
            'backgroundColor': f'{black}',
            'color': '#E5E5E5',
            'padding': '20px',
            'fontFamily': 'Inter, sans-serif',
            'fontSize': '15px',
            'lineHeight': '1.6',
            '--heading-color': '#ffffff',
            '--subtext-color': '#c0c0c0'
        }, children=[
        # model selector tabs
        dcc.Tabs(
            id='model-tabs',
            value='Ferromagnet',
            children=[
                dcc.Tab(label='Ferromagnet', value='Ferromagnet', style=tab_style, selected_style=tab_style),
                dcc.Tab(label='Election', value='Election', style=tab_style, selected_style=tab_style),
                dcc.Tab(label='Stock Market', value='Stock Market', style=tab_style, selected_style=tab_style),
            ],
            style={
                'display': 'flex',
                'width': '59%',
                'margin': '0 auto',
                'border': 'none',
                'borderRadius': '12px',
                'boxShadow': '0 2px 6px rgba(0, 0, 0, 0.4)',
                'overflow': 'hidden',
                'fontFamily': 'Inter, sans-serif',
                'backgroundColor': f'{black}',
                'height': '50px'
            },
            colors={
                'border': 'rgba(0, 0, 0, 0)',
                'primary': '#FFD700',
                'background': f'{black}'
            }
        ),

        # where per-model UI lives
        html.Div(id='model-content'),

        # single store for all model states
        dcc.Store(id='model-store', data=initial_store),

        # interval to trigger stepping
        dcc.Interval(id='step-interval', interval=400, n_intervals=0),

        # store for glow state
        dcc.Store(id='glow-store', data={'glow': True}),

        # store for faction visibility
        dcc.Store(id='faction-store', data={'show_factions': True}),
    ])
])

def create_blank_figure():
    fig = go.Figure()
    fig.update_layout(
        paper_bgcolor=f'{black}',
        plot_bgcolor=f'{black}',
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        xaxis=dict(showticklabels=False, zeroline=False),
        yaxis=dict(showticklabels=False, zeroline=False),
        margin=dict(l=0, r=0, t=0, b=0),
    )
    return fig

def button_style(is_disabled=False, button_type='play'):
    base_style = {
        'textTransform': 'uppercase',
        'letterSpacing': '1px',
        'fontSize': '17px',
        'width': '48%',
        'padding': '12px',
        'borderRadius': '10px',
        'fontWeight': '600',
        'border': 'none',
        'color': 'white',
        'boxShadow': '0 0 2px rgba(0,0,0,0.3)' if is_disabled else '0 0 12px rgba(255, 255, 255, 0.15)',
        'transition': 'all 0.3s ease-in-out',
        'cursor': 'not-allowed' if is_disabled else 'pointer',
        'opacity': 0.5 if is_disabled else 1
    }

    if is_disabled:
        base_style['backgroundColor'] = '#3a3a3a'
        base_style['fontWeight'] = '500'
    else:
        if button_type == 'play':
            base_style['backgroundImage'] = 'linear-gradient(90deg, rgb(0, 191, 255), #1266db)'
            base_style['boxShadow'] = '0 0 12px rgba(0, 191, 255, 0.5)'
        elif button_type == 'pause':
            base_style['backgroundImage'] = 'linear-gradient(90deg, orange, red)'
            base_style['boxShadow'] = '0 0 12px rgba(255, 94, 0, 0.5)'

    return base_style

@app.callback(
    Output('play-button', 'disabled'),
    Output('pause-button', 'disabled'),
    Output('play-button', 'style'),
    Output('pause-button', 'style'),
    Input('model-store', 'data'),
    State('model-tabs', 'value')
)
def update_play_pause_buttons(store_data, tab_value):
    active = store_data[tab_value]['active']

    play_disabled = active
    pause_disabled = not active

    play_style = button_style(play_disabled, 'play')
    pause_style = button_style(pause_disabled, 'pause')

    return play_disabled, pause_disabled, play_style, pause_style

def inject_button_style(disabled=False):
    style = {
        "width": "100%",
        "fontWeight": "600",
        "cursor": "not-allowed" if disabled else "pointer",
        "opacity": 0.5 if disabled else 1,
        "color": "white",
        "border": "none",
        "padding": "6px",
        "borderRadius": "8px",
        "transition": "box-shadow 0.3s ease-in-out",
        "backgroundColor": "#3a3a3a",
        "boxShadow": "0 0 10px rgba(0,0,0,0.3)"
    }

    if not disabled:
        style["backgroundImage"] = "linear-gradient(90deg, orange, red)"
        style["boxShadow"] = "0 0 12px rgba(255, 94, 0, 0.5)"

    return style

@app.callback(
    Output("inject-button", "disabled"),
    Output("inject-button", "style"),
    Input("injection-selector", "value")
)
def toggle_inject_button(event_val):
    disabled = event_val is None
    return disabled, inject_button_style(disabled)

@app.callback(
    Output("injection-selector", "value"),
    Input("inject-button", "n_clicks"),
)

def reset_dropdown_after_inject(n):
    return None  

@app.callback(
    Output('glow-store', 'data'),
    Input('glow-toggle', 'checked')
)
def toggle_glow(checked):
    return {'glow': checked}

@app.callback(
    Output('glow-toggle', 'style'),
    Input('glow-toggle', 'checked')
)
def update_glow_switch_style(is_on):
    base_style = {
        'float': 'right',
        'borderRadius': '20px',
        'transition': 'box-shadow 0.3s ease-in-out'
    }

    if is_on:
        base_style['boxShadow'] = '0 0 8px 4px rgba(0, 191, 255, 0.5)'

    return base_style

@app.callback(
    Output('faction-store', 'data'),
    Input('faction-toggle', 'checked')
)
def toggle_factions(checked):
    return {'show_factions': checked}

@app.callback(
    Output('faction-toggle', 'style'),
    Input('faction-toggle', 'checked'),
    Input('glow-store', 'data')
)
def update_faction_toggle_style(is_on, glow_data):
    glow = glow_data.get('glow', True)

    style = {
        'float': 'right',
        'borderRadius': '20px',
        'transition': 'box-shadow 0.3s ease-in-out'
    }

    if is_on and glow:
        style['boxShadow'] = '0 0 10px rgba(0, 191, 255, 0.7)'

    return style

@app.callback(
    Output('mini-initial-lattice', 'figure'),
    Input('model-tabs', 'value'),
    Input('glow-store', 'data'),
    Input('faction-store', 'data'),
    prevent_initial_call=True
)
def render_initial_lattice(tab, glow_data, faction_data):
    glow = glow_data.get('glow', True)
    show_factions = faction_data.get('show_factions', True)
    data = initial_store[tab]
    lattice = np.array(data['lattice'])
    borders_x = data['borders_x']
    borders_y = data['borders_y']
    colors = color_maps[tab]

    fig = px.imshow(lattice, color_continuous_scale=colors[::-1], origin='lower', zmax=1, zmin=-1)

    fig.update_layout(
        coloraxis_showscale=False,
        paper_bgcolor=black,
        plot_bgcolor=black,
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False, showticklabels=False, showgrid=False),
        yaxis=dict(visible=False, showticklabels=False, showgrid=False)
    )

    if show_factions:
        if glow:
            for layer in glow_layers:
                fig.add_trace(go.Scatter(
                    x=borders_x,
                    y=borders_y,
                    mode='lines',
                    line=dict(color=f'rgba({blue}, {layer["opacity"]})', width=layer['size'] * 0.7),
                    hoverinfo='skip',
                    showlegend=False,
                    cliponaxis=False
                ))

        fig.add_trace(go.Scatter(
            x=borders_x,
            y=borders_y,
            mode='lines',
            line=dict(color=white, width=1.5),
            hoverinfo='skip',
            showlegend=False,
            cliponaxis=False
        ))

    else:
        fig.add_trace(go.Scatter(
            x=[-0.5, -0.5, lattice.shape[1] - 0.5, lattice.shape[1] - 0.5],
            y=[-0.5, lattice.shape[0] - 0.5, -0.5, lattice.shape[0] - 0.5],
            mode='lines',
            line=dict(width=6, color='rgba(0, 0, 0, 0)'),
            showlegend=False,
            hoverinfo='skip'
        ))


    fig.update_traces(opacity=0.75)

    return fig

def graph_block(graph_id, title, figure, height="280px", width="100%"):
    return html.Div([
        html.Div(title, style={
            'textTransform': 'uppercase',
            'fontWeight': '500',
            'letterSpacing': '1px',
            'fontSize': '13px',
            'color': 'white',
            'marginBottom': '8px',
            'fontFamily': 'Inter, sans-serif',
            'textAlign': 'center'
        }),
        dcc.Graph(
            id=graph_id,
            figure=figure,
            config={'displayModeBar': False},
            style={
                'height': height,
                'width': width,
                'margin': '0 auto'
            }
        )
    ])


def generate_model_layout(model_name):
    store_constants = initial_store[model_name]['constants']
    return html.Div(children=[
        html.Div([

            html.Div([
                html.Button('Play', id='play-button', n_clicks=0, style=button_style(True, 'play')),
                html.Button('Pause', id='pause-button', n_clicks=0, style=button_style(False, 'pause')),
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginTop': '0px'}),

            html.Div([
                html.Div([
                    html.Span("Glow Effects", style={
                        'fontSize': '17px',
                        'textTransform': 'uppercase',
                        'fontWeight': '500',
                        'letterSpacing': '1px',
                        'color': 'white',
                        'fontFamily': 'Inter, sans-serif',}),
                    dmc.Switch(
                        id='glow-toggle',
                        checked=True,
                        size='md',
                        color=f'rgb({blue})'
                    )
                ], style={
                    'backgroundColor': '#262626',
                    'padding': '15px 25px 15px 25px',
                    'borderRadius': '8px',
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'alignItems': 'center',
                    'boxShadow': '0 0 5px rgba(0,0,0,0.3)',
                })
            ], style={'marginTop': '10px'}),

            html.Div([
                html.Div([
                    html.Span("Faction Lines", style={
                        'fontSize': '17px',
                        'textTransform': 'uppercase',
                        'fontWeight': '500',
                        'letterSpacing': '1px',
                        'color': 'white',
                        'fontFamily': 'Inter, sans-serif',}),
                    dmc.Switch(
                        id='faction-toggle',
                        checked=True,
                        size='md',
                        color=f'rgb({blue})'
                    )
                ], style={
                    'backgroundColor': '#262626',
                    'padding': '15px 25px 15px 25px',
                    'borderRadius': '8px',
                    'display': 'flex',
                    'justifyContent': 'space-between',
                    'alignItems': 'center',
                    'boxShadow': '0 0 5px rgba(0,0,0,0.3)',
                })
            ], style={'marginTop': '10px', 'marginBottom': '25px'}),

            html.Div([
                dcc.Dropdown(id='injection-selector',
                             options=event_options[model_name],
                             placeholder="Select External Event",
                             style={'color': f'{black}', 'marginBottom': '10px', 'fontSize': '16px', 'zIndex': 1002, 'position': 'relative'},),
                html.Button(
                    "Inject Event",
                    id="inject-button",
                    disabled=True,
                    style=inject_button_style(disabled=True)
                ),


            ]),

            dmc.Accordion(
                children=[
                    dmc.AccordionItem([
                        dmc.AccordionControl(
                            "Model Parameters",
                            style={
                                'backgroundColor': f'{white}',
                                'color': f'{black}',
                                'padding': '0px 12px 0px 12px',
                                'borderRadius': '5px 5px 5px 5px',
                            }
                        ),
                        dmc.AccordionPanel([
                            html.Div([
                                html.Span("Within-group influence", title="How strongly individuals follow their own group"),
                                dmc.Slider(
                                    id='J-intra-slider',
                                    min=0,
                                    max=5,
                                    step=0.1,
                                    value=store_constants['J_intra'],
                                    marks=[{"value": i, "label": str(i)} for i in range(6)],
                                    color=f"rgb({blue})",
                                    size="lg",
                                    style={
                                        'marginBottom': '25px',
                                        'backgroundColor': f'{black}'
                                    }
                                ),
                            ]),
                            html.Div([
                                html.Span("Cross-group influence", title="Tendency to be swayed by other groups"),
                                dmc.Slider(
                                    id='J-inter-slider',
                                    min=0,
                                    max=5,
                                    step=0.1,
                                    value=store_constants['J_inter'],
                                    marks=[{"value": i, "label": str(i)} for i in range(6)],
                                    color=f"rgb({blue})",
                                    size="lg",
                                    style={
                                        'marginBottom': '25px',
                                        'backgroundColor': f'{black}'
                                    }
                                ),
                            ]),
                            html.Div([
                                html.Span("Randomness (T)", title="Higher = more unpredictable"),
                                dmc.Slider(
                                    id='T-slider',
                                    min=0.01,
                                    max=5,
                                    step=0.1,
                                    value=store_constants['T'],
                                    marks=[{"value": i, "label": str(i)} for i in range(1, 6)],
                                    color=f"rgb({blue})",
                                    size="lg",
                                    style={
                                        'marginBottom': '10px',
                                        'backgroundColor': f'{black}'
                                    }
                                ),
                            ]),
                        ], style={
                            'backgroundColor': f'{black}',
                            'color': f'{white}',
                        })
                    ], 
                    value="model-params",
                    style={
                        'border': 'none',
                        'boxShadow': 'none',
                        'margin': '0',
                        'padding': '0'
                    })
                ],
                value=[],
                multiple=True,
                style={
                    'borderRadius': '5px',
                    'marginBottom': '10px',
                    'marginTop': '25px',
                }
            ),

            dmc.Accordion(
                children=[
                    dmc.AccordionItem([
                        dmc.AccordionControl(
                            "Group Biases",
                            style={
                                'backgroundColor': f'{white}',
                                'color': f'{black}',
                                'padding': '0px 12px 0px 12px',
                                'borderRadius': '5px 5px 5px 5px',
                            }
                        ),
                        dmc.AccordionPanel([
                            html.Div([
                                html.Span(f"Group {i+1} Bias", title=f"How much group {i+1} favors +1 vs. -1"),
                                dmc.Slider(
                                    id={'type': 'faction-h-slider', 'index': i},
                                    min=-1,
                                    max=1,
                                    step=0.05,
                                    value=round(state['h_map'][np.array(state['faction_map']) == i][0] / 2, 2),
                                    marks=[
                                        {"value": -1, "label": "-1"},
                                        {"value": 0.0, "label": "0"},
                                        {"value": 1, "label": "1"}
                                    ],
                                    color="orange",
                                    size="lg",
                                    style={'marginBottom': '20px'}
                                )
                            ]) for i in range(len(np.unique(state['faction_map'])))
                        ], style={
                            'backgroundColor': f'{black}',
                            'color': f'{white}',
                        })
                    ], 
                    value="group-biases",
                    style={
                        'border': 'none',
                        'boxShadow': 'none',
                        'margin': '0',
                        'padding': '0'
                    }),
                ],
                value=[],
                multiple=True,
                style={
                    'borderRadius': '5px',
                    'marginBottom': '28px',
                    'fontSize': '14px'
                }
            ),
            dcc.Graph(
                id='mini-initial-lattice',
                config={'staticPlot': True},
                style={
                    'height': '265px',
                    'width': '265px',
                    'margin': '0 auto',
                },
                figure=create_blank_figure()
            ),
        ], style={
            'width': '300px',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '20px',
            'backgroundColor': f'{black}',
            'color': f'{white}',
            'fontFamily': 'Inter, sans-serif'
        }),

        html.Div([
            html.Div([
                dcc.Graph(id='lattice-plot', config={'staticPlot': True}, figure=create_blank_figure(),
                          style={'width': '400px', 'height': '400px', 'marginRight': '125px', 'marginLeft': '35px'}),
                html.Div([
                    html.Div([
                        html.Div(gauge_titles[model_name], style={
                            'textTransform': 'uppercase',
                            'fontWeight': '500',
                            'letterSpacing': '1px',
                            'fontSize': '16px',
                            'color': 'white',
                            'width': '300px',
                            'fontFamily': 'Inter, sans-serif',
                            'textAlign': 'center'
                        }),
                        dcc.Graph(id='magnetization-gauge', config={'staticPlot': True}, figure=create_blank_figure(),
                                style={'width': '300px', 'height': '250px'})
                    ], style={'marginTop': '40px'}),

                    html.Div([
                        html.Div(agreement_titles[model_name][0], style={
                            'textTransform': 'uppercase',
                            'fontWeight': '500',
                            'letterSpacing': '1px',
                            'fontSize': '16px',
                            'color': 'white',
                            'marginBottom': '6px',
                            'fontFamily': 'Inter, sans-serif',
                            'textAlign': 'center'
                        }),
                        dcc.Graph(id='agree-bar', config={'staticPlot': True}, figure=create_blank_figure(),
                                style={'width': '300px', 'height': '160px', 'marginRight': '20px', 'marginTop': '-40px'})
                    ], style={'marginTop': '-40px',})
                ], style={
                    'display': 'flex',
                    'flexDirection': 'column',
                    'alignItems': 'center',
                    'marginRight': '60px',
                })
            ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center'}),

            html.Div([
                html.Div([
                    html.Div("      Energy Over Time", style={
                        'textTransform': 'uppercase',
                        'fontWeight': '500',
                        'letterSpacing': '1px',
                        'fontSize': '16px',
                        'color': 'white',
                        'marginBottom': '-35px',
                        'fontFamily': 'Inter, sans-serif',
                        'textAlign': 'left',
                    }),
                    dcc.Graph(id='energy-plot', config={'staticPlot': True}, figure=create_blank_figure(),
                            style={'display': 'inline-block', 'width': '100%', 'height': '280px'})
                ], style={'display': 'inline-block', 'width': '48%', 'marginRight': '25px'}),

                html.Div([
                    html.Div(spin_distribution_titles[model_name], style={
                        'textTransform': 'uppercase',
                        'fontWeight': '500',
                        'letterSpacing': '1px',
                        'fontSize': '16px',
                        'color': 'white',
                        'marginBottom': '-35px',
                        'fontFamily': 'Inter, sans-serif',
                        'textAlign': 'left',
                    }),
                    dcc.Graph(id='faction-plot', config={'staticPlot': True}, figure=create_blank_figure(),
                            style={'display': 'inline-block', 'width': '100%', 'height': '280px'})
                ], style={'display': 'inline-block', 'width': '48%'})
            ], style={'marginTop': '20px', 'display': 'flex', 'justifyContent': 'space-between'})

        ], style={
            'width': '70%', 
            'display': 'inline-block', 
            'verticalAlign': 'top',
            'marginLeft': '75px',
            'marginRight': '0px',
            'marginBottom': '0px',
            })
    ])


@app.callback(
    Output('model-content','children'),
    Input('model-tabs','value')
)
def render_tab(tab):
    return generate_model_layout(tab)

@app.callback(
    Output('model-store', 'data'),
    [
        Input('model-tabs', 'value'),
        Input('step-interval', 'n_intervals'),
        Input('J-intra-slider', 'value'),
        Input('J-inter-slider', 'value'),
        Input('T-slider', 'value'),
        Input('inject-button', 'n_clicks'),
        Input('play-button', 'n_clicks'),
        Input('pause-button', 'n_clicks'),
        Input({'type': 'faction-h-slider', 'index': ALL}, 'value'),
    ],
    [
        State('injection-selector', 'value'),
        State('model-store', 'data')
    ]
)

def update_model_store(tab,
                       n_intervals,
                       J_intra,
                       J_inter,
                       T_val,
                       inject_clicks,
                       play_clicks,
                       pause_clicks,
                       faction_h_values,
                       inject_event,
                       store_data):
    ctx = callback_context.triggered[0]['prop_id'].split('.')[0]

    if ctx == 'model-tabs':
        for m in store_data:
            store_data[m]['active'] = False
        store_data[tab]['active'] = True
        return store_data

    if ctx == 'step-interval' and store_data[tab]['active']:
        models[tab].step(num_steps=1)
        
        state = models[tab].get_current_state()
        sd = store_data[tab]
        
        sd['lattice'] = state['lattice'].tolist()
        sd['energies'] = state['energies'].tolist()
        sd['current_trial'] = state['current_trial']

        if state['current_trial'] % 10 == 0:
            sd['snapshots'].append({
                'lattice': state['lattice'].tolist(),
                'energies': state['energies'].tolist(),
                'trial': state['current_trial']
            })

        store_data[tab] = sd
        return store_data


    if ctx in ['J-intra-slider', 'J-inter-slider', 'T-slider']:
        sim = models[tab]
        sim.J_intra = J_intra
        sim.J_inter = J_inter
        sim.T = T_val

        store_data[tab]['constants'].update({
            'J_intra': J_intra,
            'J_inter': J_inter,
            'T': T_val
        })

        return store_data
    
    if ctx == 'play-button' and play_clicks > 0:
        store_data[tab]['active'] = True
        return store_data

    if ctx == 'pause-button' and pause_clicks > 0:
        store_data[tab]['active'] = False
        return store_data

    if ctx == 'inject-button' and inject_clicks > 0 and inject_event:
        value = event_mapping.get(inject_event)
        models[tab].inject_event(value)
        
        state = models[tab].get_current_state()
        store_data[tab].update({
            'lattice':       state['lattice'].tolist(),
            'energies':      state['energies'].tolist(),
            'current_trial': state['current_trial'],
        })
        return store_data
    
    if ctx == "{'type':'faction-h-slider','index':":
        sim = models[tab]
        slider_inputs = dash.callback_context.inputs
        for k, val in slider_inputs.items():
            if isinstance(k, dict) and k.get('type') == 'faction-h-slider':
                group_index = k.get('index')
                sim.adjust_constants(faction_id=group_index, new_h=val * 2)
        state = sim.get_current_state()
        store_data[tab]['h_map'] = state['h_map'].tolist()
        return store_data

    return store_data

@app.callback(
    Output('magnetization-gauge', 'figure'),
    Output('agree-bar', 'figure'),
    Output('lattice-plot','figure'),
    Output('energy-plot','figure'),
    Output('faction-plot','figure'),
    Input('model-store','data'),
    Input('glow-store', 'data'),
    Input('faction-store', 'data'),
    State('model-tabs','value'),
    prevent_initial_call=True
)
def update_graphs(store_data, glow_data, faction_data, tab):
    sd = store_data[tab]
    lattice = np.array(sd['lattice'])
    energies = np.array(sd['energies'])
    energies = energies - energies[0]
    faction_map = np.array(sd['faction_map'])

    colors = color_maps[tab]
    char_map = character_maps[tab]
    glow = glow_data.get('glow', True)
    show_factions = faction_data.get('show_factions', True)

    mag = models[tab].get_magnetization()

    blue_layers = [
        {"opacity": 0.08, "bar_thickness": 0.575, "line_width": 15,  "threshold_thickness": 0.92},
        {"opacity": 0.12, "bar_thickness": 0.45,  "line_width": 12,  "threshold_thickness": 0.825},
        {"opacity": 0.25, "bar_thickness": 0.35,  "line_width": 9,   "threshold_thickness": 0.725},
        {"opacity": 0.4,  "bar_thickness": 0.275, "line_width": 7,   "threshold_thickness": 0.65},
        {"opacity": 0.65, "bar_thickness": 0.2,   "line_width": 5.5, "threshold_thickness": 0.6},
    ]

    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=mag,
        # title={'text': gauge_titles[tab], 'font': {'color': f'{white}'}},
        number={'valueformat': ".2f"},
        gauge={
            'axis': {'range': [-1, 1], 'tickvals': [-1, -0.5, 0, 0.5, 1]},
            'bar': {
                'color': f"rgba({blue}, {blue_layers[0]['opacity']})" if glow else "rgba(255, 255, 255, 1)",
                'thickness': blue_layers[0]['bar_thickness'] if glow else 0.15
            },
            'bgcolor': "rgba(0, 0, 0, 0)",
            'steps': [
                {'range': [-1, 0], 'color': color_maps[tab][1]},
                {'range': [0, 1], 'color': color_maps[tab][0]}
            ],
            'threshold': {
                'line': {
                    'color': f"rgba({blue}, {blue_layers[0]['opacity']})" if glow else "rgba(255, 255, 255, 1)",
                    'width': blue_layers[0]['line_width'] if glow else 4.5
                },
                'thickness': blue_layers[0]['threshold_thickness'] if glow else 0.565,
                'value': mag
            }
        },
        domain={'x': [0, 1], 'y': [0.35, 1]},
    ))


    if glow:
        for layer in blue_layers[1:]:
            color = f"rgba({blue}, {layer['opacity']})"
            fig_gauge.add_trace(go.Indicator(
                mode="gauge",
                value=mag,
                gauge={
                    'axis': {'range': [-1, 1], 'visible': False},
                    'bar': {'color': 'rgba(0,0,0,0)'},
                    'bgcolor': 'rgba(0,0,0,0)',
                    'steps': [],
                    'bar': {'color': color, 'thickness': layer["bar_thickness"]},
                    'threshold': {
                        'line': {'color': color, 'width': layer["line_width"]},
                        'thickness': layer["threshold_thickness"],
                        'value': mag
                    }
                },
                domain={'x': [0, 1], 'y': [0.35, 1]},
            ))

        fig_gauge.add_trace(go.Indicator(
            mode="gauge",
            value=mag,
            gauge={
                'axis': {'range': [-1, 1], 'visible': False},
                'bar': {'color': 'rgba(0,0,0,0)'},
                'bgcolor': 'rgba(0,0,0,0)',
                'steps': [],
                'bar': {'color': "rgba(255, 255, 255, 1)", 'thickness': 0.15},
                'threshold': {
                    'line': {'color': "rgba(255, 255, 255, 1)", 'width': 4.5},
                    'thickness': 0.565,
                    'value': mag
                }
            },
            domain={'x': [0, 1], 'y': [0.35, 1]},
        ))



    fig_gauge.update_layout(
        paper_bgcolor="rgba(0, 0, 0, 0)",
        font=dict(color=f"{white}", family="Inter, sans-serif", size=12),
        height=280,
        width=280,
        margin=dict(t=0, b=0, l=20, r=20)
    )
    
    agreement_score = models[tab].get_agreement_score()
    agreement_score = (agreement_score * 2) - 1

    scale = 5
    adjusted = (np.log1p(scale * agreement_score) / np.log1p(scale))
    agreement_score = max(0, min(1, adjusted))

    fig_agree = go.Figure()

    z = np.linspace(0, 1, 500).reshape(1, -1)

    agreement_title, left_label, right_label = agreement_titles.get(tab, ("Local Agreement", "Low", "High"))

    fig_agree = go.Figure()

    z = np.linspace(0, 1, 500).reshape(1, -1)
    fig_agree.add_trace(go.Heatmap(
        z=z,
        x=np.linspace(-0.3, 1.3, z.shape[1]),
        y=[0.5],
        colorscale=[
            [0.0, "rgb(100,0,0)"],
            [0.5, "rgb(18,18,18)"],
            [1.0, "rgb(0,100,0)"]
        ],
        zmin=0, zmax=1,
        showscale=False,
        hoverinfo='skip'
    ))

    if glow:
        for layer in glow_layers:
            fig_agree.add_trace(go.Scatter(
                x=[agreement_score],
                y=[0.5],
                mode="markers",
                marker=dict(
                    color=f'rgba({blue}, {layer["opacity"]})',
                    size=layer["size"] + 11
                ),
                hoverinfo='skip',
                showlegend=False
            ))


    fig_agree.add_trace(go.Scatter(
        x=[agreement_score],
        y=[0.5],
        mode="markers+text",
        marker=dict(size=12, color=f"{white}"),
        text=[f"{agreement_score:.2f}"],
        textfont=dict(color=f"{white}"),
        textposition="top center",
        hoverinfo="skip",
        showlegend=False
    ))

    fig_agree.add_annotation(
        x=-0.13, y=0.5, text=left_label, showarrow=False, textangle=90,
        font=dict(color=f"{white}", size=(12 if(tab == 2) else 11))
    )
    fig_agree.add_annotation(
        x=1.13, y=0.5, text=right_label, showarrow=False, textangle=-90,
        font=dict(color=f"{white}", size=(12 if(tab == 2) else 11))
    )

    fig_agree.update_layout(
        # title=dict(text=agreement_title, font=dict(color=f"{white}"), x=0.5),
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color=f"{white}", family="Inter, sans-serif", size=12),
        height=120,
        margin=dict(l=20, r=20, t=40, b=10),
        xaxis=dict(range=[-0.2, 1.2], visible=False, showticklabels=False),
        yaxis=dict(range=[0, 1], visible=False, showticklabels=False)
    )

    fig_lattice = px.imshow(lattice,
                    color_continuous_scale=colors[::-1],
                    origin='lower',
                    zmax=1,
                    zmin=-1)

    
    fig_lattice.update_layout(
        coloraxis_showscale=False,
        paper_bgcolor=f'{black}',
        plot_bgcolor=f'{black}',
        font=dict(color=f"{white}", family="Inter, sans-serif", size=12),
        margin=dict(l=0, r=0, t=0, b=0),

        xaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.5, lattice.shape[1]-0.5],
            visible=False,
            constrain="domain"
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            range=[-0.5, lattice.shape[0]-0.5],
            visible=False,
            scaleanchor="x",
            scaleratio=1
        ),
    )


    fig_lattice.update_layout(dragmode=False, uirevision='static', modebar_remove=['zoom', 'pan', 'select', 'lasso', 'resetScale2d'])

    borders_x = sd.get('borders_x', [])
    borders_y = sd.get('borders_y', [])

    if show_factions:
        if glow:
            for layer in glow_layers:
                fig_lattice.add_trace(go.Scatter(
                    x=borders_x,
                    y=borders_y,
                    mode='lines',
                    line=dict(
                        color=f'rgba({blue}, {layer["opacity"]})',
                        width=layer["size"]
                    ),
                    hoverinfo='skip',
                    showlegend=False
                ))

        fig_lattice.add_trace(go.Scatter(
            x=borders_x,
            y=borders_y,
            mode='lines',
            line=dict(color=f'{white}', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))

        labels = sd.get('labels', [])
        for x, y, label_num in labels:
            fig_lattice.add_shape(
                type="circle",
                xref="x", yref="y",
                x0=x-0.7, y0=y-0.7, x1=x+0.7, y1=y+0.7,
                line_color=f"{white}",
                fillcolor=f"{black}",
                opacity=0.5
            )
            fig_lattice.add_annotation(
                x=x,
                y=y,
                text=str(label_num),
                font=dict(color=f"{white}", size=12),
                showarrow=False
            )
    else:
        fig_lattice.add_trace(go.Scatter(
            x=[-0.5, -0.5, lattice.shape[1] - 0.5, lattice.shape[1] - 0.5],
            y=[-0.5, lattice.shape[0] - 0.5, -0.5, lattice.shape[0] - 0.5],
            mode='lines',
            line=dict(width=6, color='rgba(0, 0, 0, 0)'),
            showlegend=False,
            hoverinfo='skip'
        ))

    text_x = []
    text_y = []
    text_values = []

    for r in range(lattice.shape[0]):
        for c in range(lattice.shape[1]):
            spin = lattice[r, c]
            symbol = char_map.get(spin, '')
            text_x.append(c)
            text_y.append(r)
            text_values.append(symbol)

    fig_lattice.add_trace(go.Scatter(
        x=text_x,
        y=text_y,
        text=text_values,
        mode='text',
        textfont=dict(color=f'{white}', size=9),
        opacity=0.4,
        hoverinfo='skip',
        showlegend=False
    ))

    fig_energy = go.Figure()

    if glow:

        for layer in glow_layers:
            fig_energy.add_trace(go.Scatter(
                y=energies,
                mode='lines',
                line=dict(
                    color=f'rgba({blue}, {layer["opacity"]})',
                    width=layer["size"]
                ),
                hoverinfo='skip',
                showlegend=False
            ))

    fig_energy.add_trace(go.Scatter(
        y=energies,
        mode='lines',
        line=dict(
            color=f'{white}',
            width=2
        ),
        hoverinfo='skip',
        name='Energy'
    ))


    fig_energy.update_layout(
        margin=dict(t=45, b=20, l=20, r=20),
        paper_bgcolor='rgba(0, 0, 0, 0)', plot_bgcolor='rgba(0, 0, 0, 0)',
        showlegend=False,
        font=dict(color=f"{white}", family="Inter, sans-serif", size=12),
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(
            showgrid=False,
            ticksuffix=' '
        ))
    
    fig_energy.update_layout(dragmode=False, uirevision='static', modebar_remove=['zoom', 'pan', 'select', 'lasso', 'resetScale2d'])
    
    faction_map = models[tab].faction_map
    bars = []
    for f in np.unique(faction_map):
        mask = (faction_map==f)
        total = mask.sum()
        net   = lattice[mask].sum()
        bars.append(100*net/total if total else 0)

    fig_distribution = px.bar(
        x=list(range(1, len(bars)+1)),
        y=bars,
    )
    fig_distribution.update_layout(
        margin=dict(t=60, b=20, l=20, r=20),
        xaxis=dict(tickmode='linear', dtick=1),
        xaxis_title=None,
        yaxis=dict(
            range=[-100, 100], 
            ticktext=["100% ", "50% ", "0% ", "–50% ", "–100% "], 
            tickvals=[100, 50, 0, -50, -100],
        ),
        yaxis_title=None,
        paper_bgcolor='rgba(0, 0, 0, 0)',
        plot_bgcolor='rgba(0, 0, 0, 0)',
        font=dict(color=f"{white}", family="Inter, sans-serif", size=12),
    )

    fig_distribution.update_traces(marker_line_width=0, width=0.6, marker_color=[colors[0] if bar > 0 else colors[1] for bar in bars])

    fig_distribution.update_layout(dragmode=False, uirevision='static', modebar_remove=['zoom', 'pan', 'select', 'lasso', 'resetScale2d'])

    return fig_gauge, fig_agree, fig_lattice, fig_energy, fig_distribution

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)