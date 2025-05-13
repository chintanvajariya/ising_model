import numpy as np

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
    'oscillate_field': lambda: np.random.choice([-0.3, 0.3]),
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


tab_style = {
    'padding': '13px 0px',
    'fontWeight': '500',
    'fontSize': '15px',
    'letterSpacing': '1px',
    'fontFamily': 'Inter, sans-serif',
    'textTransform': 'uppercase',
    'color': 'white',
    'backgroundColor': '#262626',
    'border': 'none',
}

selected_tab_style = {
    **tab_style,
    'color': 'black',
    'backgroundColor': 'white',
}

scale_val = 500