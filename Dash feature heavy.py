import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, ALL
import inspect

from analysis_tools import TOOL_REGISTRY

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H4("Analysis Suite", className="mb-3"),
                
                html.Label("Select Tool:", className="fw-bold"),
                dcc.Dropdown(
                    id='tool-selector',
                    options=list(TOOL_REGISTRY.keys()),
                    value=list(TOOL_REGISTRY.keys())[0] if TOOL_REGISTRY else None,
                    clearable=False,
                    className="mb-3"
                ),
                
                html.Div(id='dynamic-inputs-container', className="mb-3"),
                
                # --- NEW: ESTIMATED TIME DISPLAY BADGE ---
                html.Div(id='runtime-estimation-badge', className="mb-3 text-center"),
                
                dbc.Button("Run Analysis", id='run-btn', color="primary", className="w-100 mb-4"),
                
            ], className="p-4 border rounded bg-light shadow-sm")
        ], md=5, className="mx-auto mt-5")
    ])
], fluid=True)

# (Keep your existing generate_ui_inputs callback here...)

# ---------------------------------------------------------------------
# NEW CALLBACK: Calculate & Display Estimated Runtime
# ---------------------------------------------------------------------
@app.callback(
    Output('runtime-estimation-badge', 'children'),
    Input('tool-selector', 'value'),
    Input({'type': 'dynamic-input', 'name': ALL}, 'value'), # Listens to every active input
    State({'type': 'dynamic-input', 'name': ALL}, 'id')
)
def update_estimated_time(tool_name, input_values, input_ids):
    if not tool_name or tool_name not in TOOL_REGISTRY:
        return ""
        
    func = TOOL_REGISTRY[tool_name]
    
    # If the developer didn't provide an estimated_times map, default gracefully
    if not hasattr(func, 'estimated_times'):
        return dbc.Badge("⏱️ Est. Runtime: Instant", color="secondary", className="p-2 w-100")
        
    # We need to make sure the user's active inputs match the order of the function parameters
    signature = inspect.signature(func)
    param_order = list(signature.parameters.keys())
    
    # Map the current values to their parameter names
    current_inputs = {id_dict['name']: val for val, id_dict in zip(input_values, input_ids)}
    
    # Build a tuple of values sorted perfectly by the function's argument order
    try:
        user_combination = tuple(current_inputs[param] for param in param_order if param in current_inputs)
        
        # Look up the combination in the developer's dictionary map
        if user_combination in func.estimated_times:
            est_duration = func.estimated_times[user_combination]
            
            # Change badge color to warning (yellow/orange) if it's a long calculation
            is_heavy = "minute" in est_duration or (any(char.isdigit() for char in est_duration) and int(''.join(filter(str.isdigit(), est_duration))) > 5)
            badge_color = "warning" if is_heavy else "info"
            
            return dbc.Badge(f"⏱️ Est. Runtime: {est_duration}", color=badge_color, className="p-2 w-100 fs-6")
    except KeyError:
        # Happens momentarily during dynamic UI rebuilding when switches happen
        return ""
        
    # Fallback if a specific combination wasn't explicitly mapped by the developer
    return dbc.Badge("⏱️ Est. Runtime: Variable", color="light", className="text-dark p-2 w-100")


if __name__ == '__main__':
    app.run_server(debug=True)
  
