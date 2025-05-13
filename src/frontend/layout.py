from dash import dcc, html
import dash_mantine_components as dmc
import numpy as np

from .constants import black, white, blue, tab_style, event_options, gauge_titles, agreement_titles, spin_distribution_titles, selected_tab_style, scale_val
from .helpers import create_blank_figure, inject_button_style, button_style

def create_app_layout(initial_store):
    default_model = 'Ferromagnet'
    state = initial_store[default_model]['state']
    constants = initial_store[default_model]['constants']

    return dmc.MantineProvider(
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
                # Tabs
                dcc.Tabs(
                    id='model-tabs',
                    value=default_model,
                    children=[
                        dcc.Tab(label='Ferromagnet', value='Ferromagnet', style=tab_style, selected_style=selected_tab_style),
                        dcc.Tab(label='Election', value='Election', style=tab_style, selected_style=selected_tab_style),
                        dcc.Tab(label='Stock Market', value='Stock Market', style=tab_style, selected_style=selected_tab_style),
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
                    }
                ),

                # Initial tab content (static so Dash sees component IDs)
                html.Div(
                    id='model-content',
                    children=generate_model_layout(default_model, state, constants)
                ),

                # Other stores and interval
                dcc.Store(id='model-store', data=initial_store,storage_type='memory'),
                dcc.Store(id='glow-store', data={'glow': True}, storage_type='memory'),
                dcc.Store(id='faction-store', data={'show_factions': True}, storage_type='memory'),
                dcc.Interval(id='step-interval', interval=400, n_intervals=0)
            ])
        ]
    )


def generate_model_layout(model_name, state, store_constants):
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
                                    id={'type': 'J-intra-slider', 'index': model_name},
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
                                    id={'type': 'J-inter-slider', 'index': model_name},
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
                                    id={'type': 'T-slider', 'index': model_name},
                                    min=0.1,
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
                                    value = round(np.array(state['h_map'])[np.array(state['faction_map']) == i][0] / scale_val, 2) 
                                                  if np.array(state['h_map'])[np.array(state['faction_map']) == i].size > 0 
                                                  else 0.0,
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