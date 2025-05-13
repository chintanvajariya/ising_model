import dash
from backend import IsingSim
from frontend.layout import create_app_layout
from frontend.callbacks import register_callbacks
from frontend.helpers import compute_faction_borders, compute_faction_labels

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[
        'https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap'
    ]
)
server = app.server

models_container = {}
register_callbacks(app, models_container)

def generate_fresh_layout():
    models = {
        'Ferromagnet': IsingSim(N=20),
        'Election':     IsingSim(N=20),
        'Stock Market': IsingSim(N=20)
    }

    initial_store = {}
    for name, model in models.items():
        state = model.get_current_state()
        borders_x, borders_y = compute_faction_borders(state['faction_map'])
        labels = compute_faction_labels(state['faction_map'])

        initial_store[name] = {
            "state": state,
            "constants": {
                "J_intra": model.J_intra,
                "J_inter": model.J_inter,
                "T": model.T,
            },
            "active": name == "Ferromagnet",
            "lattice": state['lattice'].tolist(),
            "faction_map": state['faction_map'].tolist(),
            "h_map": state['h_map'].tolist(),
            "energies": state['energies'].tolist(),
            "current_trial": state['current_trial'],
            "snapshots": [],
            "borders_x": borders_x,
            "borders_y": borders_y,
            "labels": labels,
        }

    models_container.clear()
    models_container.update(models)

    return create_app_layout(initial_store)

app.layout = generate_fresh_layout

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=True)
