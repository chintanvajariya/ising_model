import numpy as np
from dash import html, dcc
import plotly.graph_objects as go
import dash_mantine_components as dmc

from .constants import black


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

