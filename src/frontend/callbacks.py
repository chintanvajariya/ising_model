import dash
import numpy as np
from dash import Input, Output, State, callback_context, ALL
import plotly.graph_objects as go
import plotly.express as px

from src.backend import inject_event
from .constants import color_maps, character_maps, glow_layers, blue, white, black, agreement_titles, event_mapping, scale_val
from .helpers import button_style, inject_button_style
from .layout import generate_model_layout

def register_callbacks(app, models):
    @app.callback(
        Output('model-store', 'data'),
        [
            Input('model-tabs', 'value'),
            Input('step-interval', 'n_intervals'),
            Input({'type': 'J-intra-slider', 'index': ALL}, 'value'),
            Input({'type': 'J-inter-slider', 'index': ALL}, 'value'),
            Input({'type': 'T-slider', 'index': ALL}, 'value'),
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
                        inject_event_val,
                        store_data):

        triggered_props = callback_context.triggered
        triggered_ids = [t['prop_id'].split('.')[0] for t in triggered_props]

        if not store_data or tab not in store_data:
            print(f"No store_data or tab '{tab}' not found.")
            return dash.no_update

        sim = models[tab]

        if 'model-tabs' in triggered_ids:
            for m in store_data:
                store_data[m]['active'] = False
            store_data[tab]['active'] = True
            print(f"Activated model: {tab}")
            return store_data

        if 'step-interval' in triggered_ids and store_data[tab]['active']:
            sim.step(num_steps=1)
            state = sim.get_current_state()

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

        if any(k in triggered_ids for k in [
            '{"index":"%s","type":"J-intra-slider"}' % tab,
            '{"index":"%s","type":"J-inter-slider"}' % tab,
            '{"index":"%s","type":"T-slider"}' % tab
        ]):
            sim.J_intra = J_intra[0]
            sim.J_inter = J_inter[0]
            sim.T = T_val[0]

            store_data[tab]['constants'].update({
                'J_intra': sim.J_intra,
                'J_inter': sim.J_inter,
                'T': sim.T
            })

            print(f"Updated constants => J_intra={sim.J_intra}, J_inter={sim.J_inter}, T={sim.T}")
            return store_data

        if 'play-button' in triggered_ids and play_clicks > 0:
            store_data[tab]['active'] = True
            print(f"Play clicked => Activated: {tab}")
            return store_data

        if 'pause-button' in triggered_ids and pause_clicks > 0:
            store_data[tab]['active'] = False
            print(f"Pause clicked => Paused: {tab}")
            return store_data

        if 'inject-button' in triggered_ids and inject_clicks and inject_event_val:
            value = event_mapping.get(inject_event_val)
            if callable(value):
                value = value()
            inject_event(sim.lattice, value, sim.random)

            state = sim.get_current_state()
            store_data[tab].update({
                'lattice': state['lattice'].tolist(),
                'energies': state['energies'].tolist(),
                'current_trial': state['current_trial']
            })

            print(f"Injected event '{inject_event}' with strength {value}")
            return store_data

        if any("faction-h-slider" in tid for tid in triggered_ids):
            print(f"Updating h_map from faction sliders")

            for idx, val in enumerate(faction_h_values):
                scaled_h = val * scale_val
                sim.adjust_constants(faction_id=idx, new_h=scaled_h)

                mask = sim.faction_map == idx
                avg_spin = sim.lattice[mask].mean()
                print(f"Faction {idx} => avg_spin = {avg_spin:.3f} after h = {scaled_h:.2f}")

            state = sim.get_current_state()
            store_data[tab]['h_map'] = state['h_map'].tolist()
            return store_data

        return store_data

    
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
            style['boxShadow'] = '0 0 8px 4px rgba(0, 191, 255, 0.5)'

        return style

    @app.callback(
        Output('mini-initial-lattice', 'figure'),
        Input('model-tabs', 'value'),
        Input('glow-store', 'data'),
        Input('faction-store', 'data'),
        State('model-store', 'data'),
        prevent_initial_call=True
    )
    def render_initial_lattice(tab, glow_data, faction_data, store_data):
        data = store_data[tab]
        glow = glow_data.get('glow', True)
        show_factions = faction_data.get('show_factions', True)
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
    
    @app.callback(
        Output('model-content','children'),
        Input('model-tabs','value'),
        State('model-store', 'data')
    )
    def render_tab(tab, store_data):
        state = {
            'faction_map': store_data[tab]['faction_map'],
            'h_map': store_data[tab]['h_map']
        }
        store_constants = store_data[tab]['constants']
        return generate_model_layout(tab, state, store_constants)

    
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