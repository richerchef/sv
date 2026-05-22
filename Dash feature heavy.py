import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, ALL, ctx
import pandas as pd
import plotly.express as px
import plotly.io as pio
import datetime
import inspect
import time
from urllib.parse import parse_qs, urlencode

# ---------------------------------------------------------------------
# 1. THE MOCK FUNCTION REGISTRY (Simulating your external package files)
# ---------------------------------------------------------------------

def run_sensor_variance(sensor_id: ['Sensor_A', 'Sensor_B', 'Sensor_C'], threshold: float = 1.5):
    """
    Calculates rolling variance anomalies for hardware sensors.
    Select Sensor_C or set a low threshold to generate higher anomaly flags.
    """
    # Simulate data processing
    timestamps = pd.date_range(start="2026-01-01", periods=10, freq="h")
    
    # Scale calculations based on user input
    multiplier = 2.0 if sensor_id == 'Sensor_C' else 1.0
    variances = [0.5, 0.8, 1.2 * multiplier, 0.9, 1.7 * multiplier, 2.1, 0.6, 1.1, 1.4, 0.8]
    
    df = pd.DataFrame({'Timestamp': timestamps, 'Variance': variances})
    df['Anomaly'] = df['Variance'] > threshold
    
    # Build chart
    fig = px.line(df, x='Timestamp', y='Variance', title=f"Variance Over Time: {sensor_id}")
    fig.add_hline(y=threshold, line_dash="dash", line_color="red", annotation_text=f"Threshold ({threshold})")
    fig.update_layout(template="plotly_white")
    
    return {
        "dataframe": df,
        "figure": fig,
        "summary_text": f"Successfully calculated variance metrics. Found {df['Anomaly'].sum()} anomalies exceeding threshold {threshold}."
    }

# Attach the estimation runtime metadata directly to the function object
run_sensor_variance.estimated_times = {
    ('Sensor_A', 1.5): "Under 1 second",
    ('Sensor_B', 1.5): "Under 1 second",
    ('Sensor_C', 1.5): "3-4 seconds (Heavy streams)",
}


def run_hvac_efficiency(system_zone: ['Zone_1', 'Zone_2'], configuration: ['Standard', 'Deep_Optimization']):
    """
    Computes thermodynamic efficiency metrics for building HVAC systems.
    Warning: Deep Optimization takes longer to calculate due to multi-node sorting.
    """
    # Simulate loading process if user picks heavy calculations
    if configuration == 'Deep_Optimization':
        time.sleep(1) # Visual slowdown simulation
        efficiency_scores = [88.4, 91.2, 94.1, 95.8]
    else:
        efficiency_scores = [72.1, 74.5, 78.2, 79.0]
        
    df = pd.DataFrame({
        'Quarter': ['Q1', 'Q2', 'Q3', 'Q4'],
        'Efficiency_Score': efficiency_scores,
        'Target_Score': [80.0, 80.0, 85.0, 85.0]
    })
    
    fig = px.bar(df, x='Quarter', y=['Efficiency_Score', 'Target_Score'], barmode='group', title=f"HVAC Yield: {system_zone}")
    fig.update_layout(template="plotly_white")
    
    return {
        "dataframe": df,
        "figure": fig,
        "summary_text": f"Completed climate efficiency log using config framework: [{configuration}]."
    }

# Attach runtime metadata mapping to arguments in exact order of signature
run_hvac_efficiency.estimated_times = {
    ('Zone_1', 'Standard'): "Instant",
    ('Zone_2', 'Standard'): "Instant",
    ('Zone_1', 'Deep_Optimization'): "5-8 seconds",
    ('Zone_2', 'Deep_Optimization'): "8-10 seconds (Multi-Grid)",
}

# Master compiled mapping dictionary used by UI loader
TOOL_REGISTRY = {
    "Sensor Variance": run_sensor_variance,
    "HVAC Efficiency": run_hvac_efficiency
}


# ---------------------------------------------------------------------
# 2. CORE DASH APPLICATION & LAYOUT DESIGN
# ---------------------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

app.layout = dbc.Container([
    # Dynamic URL interface tracking
    dcc.Location(id='url', refresh=False),
    
    # Download interfaces
    dcc.Download(id="download-csv"),
    dcc.Download(id="download-html-fig"),
    dcc.Download(id="download-report"),
    
    # Header Area
    html.Header([
        dbc.Container([
            dbc.Row([
                dbc.Col(html.H1("Dynamic Engineering Core", className="m-0 h3 text-white"), xs=8),
                dbc.Col(
                    dbc.Button("📘 Developer Docs", id="open-docs-btn", color="link", className="text-white text-decoration-none p-0 float-end mt-1"),
                    xs=4
                )
            ])
        ], fluid=True)
    ], className="bg-dark py-3 mb-4 shadow-sm"),

    # Main Body Panel Grid
    dbc.Container([
        dbc.Row([
            
            # Left Configuration Sidebar Panel
            dbc.Col([
                html.Div([
                    html.H5("Execution Controls", className="mb-3 border-bottom pb-2 fw-bold"),
                    
                    html.Label("Select Active Analytics Module:", className="small fw-semibold text-muted"),
                    dcc.Dropdown(
                        id='tool-selector',
                        options=list(TOOL_REGISTRY.keys()),
                        value=list(TOOL_REGISTRY.keys())[0],
                        clearable=False,
                        className="mb-3"
                    ),
                    
                    # Dynamically injected controls mount here
                    html.Div(id='dynamic-inputs-container', className="mb-3"),
                    
                    # Real-time reactive estimated runtime badge area
                    html.Div(id='runtime-estimation-badge', className="mb-3 text-center"),
                    
                    dbc.Button("🚀 Run Analysis Execution", id='run-btn', color="primary", className="w-100 mb-2"),
                    
                    # Collapsible File Export Action utility dock
                    html.Div([
                        html.Hr(),
                        html.H6("Export Utilities", className="fw-bold text-muted small mb-2"),
                        dbc.Button("📥 Download Data (CSV)", id="btn-csv", color="success", size="sm", className="w-100 mb-2"),
                        dbc.Button("📊 Download Interactive Chart (HTML)", id="btn-chart", color="info", size="sm", className="w-100 mb-2"),
                        dbc.Button("📄 Generate Audit Report (MD)", id="btn-report", color="secondary", size="sm", className="w-100")
                    ], id="export-panel", style={"display": "none"})
                    
                ], className="p-4 border rounded bg-light shadow-sm")
            ], md=4, className="mb-4"),
            
            # Right Workspace Presentation Area
            dbc.Col([
                html.Div([
                    html.Div(id='text-summary-box', className="mb-3 p-3 bg-white border rounded shadow-sm text-secondary font-monospace style-italic", style={"display": "none"}),
                    dcc.Graph(id='main-chart-display', style={"display": "none"}),
                    html.Div(id='table-display-container', className="mt-4")
                ])
            ], md=8)
            
        ])
    ], fluid=True),

    # ---------------------------------------------------------------------
    # ON-SCREEN DEVELOPER INSTRUCTION MANUAL MODAL DIALOG
    # ---------------------------------------------------------------------
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Package Reference: Creating Custom UI Functions")),
        dbc.ModalBody(
            dcc.Markdown("""
            This architecture automatically constructs UI inputs by running runtime reflection across your custom functions. 

            ### 📋 Core Integration Rules
            1. **Function Mapping Template:** Functions must accept baseline configurations and generate packaged return outputs.
            2. **Docstrings:** Use functional multi-line comments. The engine reads these text blocks automatically to generate context labels.
            3. **Structured Returns:** Your function must output a dictionary containing:
               - `"dataframe"`: A Pandas DataFrame configuration.
               - `"figure"`: A generated interactive Plotly chart figure.
               - `"summary_text"`: A summary reporting status layout string.

            ### ⚙️ Type Hint Layout Syntax Definitions
            - **Dropdowns (List Collections):** `arg_name: ['OptionA', 'OptionB']`
            - **Numeric Inputs (Types):** `arg_name: float = 1.5` or `arg_name: int = 10`
            - **Free Text Entry:** `arg_name: str = "Query"`

            ### ⏱️ Runtime Estimations Mapping
            To trigger active latency estimations on-screen, hook a dictionary tracking parameter tuples to the end of your function block:
```python
            def run_example(mode: ['Fast', 'Slow']):
                ...
            run_example.estimated_times = {
                ('Fast',): "Under 1 second",
                ('Slow',): "45 seconds (Heavy Query)"
            }
            ```
            """)
        ),
        dbc.ModalFooter(dbc.Button("Close Documentation Window", id="close-docs-btn", className="ms-auto", color="secondary")),
    ], id="docs-modal", size="xl", is_open=False)
], fluid=True)


# ---------------------------------------------------------------------
# 3. INTERACTIVE CALLBACK BACKEND PIPELINES
# ---------------------------------------------------------------------

# --- Global In-Memory Execution Caching Slots ---
CURRENT_DF = None
CURRENT_FIG = None
CURRENT_META = {}

# PIPELINE 1: Toggle Developer Manual Modal Popup
@app.callback(
    Output("docs-modal", "is_open"),
    [Input("open-docs-btn", "n_clicks"), Input("close-docs-btn", "n_clicks")],
    [State("docs-modal", "is_open")],
)
def toggle_docs_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open


# PIPELINE 2: Introspect Signature & Build HTML Form Inputs Automatically
@app.callback(
    Output('dynamic-inputs-container', 'children'),
    Input('tool-selector', 'value')
)
def generate_dynamic_form_ui(selected_tool_name):
    if not selected_tool_name or selected_tool_name not in TOOL_REGISTRY: 
        return "Select a valid tool module."
        
    func = TOOL_REGISTRY[selected_tool_name]
    signature = inspect.signature(func)
    ui_elements = []
    
    if func.__doc__:
        ui_elements.append(html.P(func.__doc__, className="text-muted small lh-sm p-2 bg-white border rounded mb-3"))

    for param_name, param in signature.parameters.items():
        formatted_label = param_name.replace('_', ' ').title()
        
        if isinstance(param.annotation, list):
            element = html.Div([
                html.Label(f"{formatted_label}:", className="small fw-semibold mt-2"),
                dcc.Dropdown(
                    options=param.annotation,
                    value=param.annotation[0],
                    id={'type': 'dynamic-input', 'name': param_name},
                    clearable=False
                )
            ])
        else:
            default_val = param.default if param.default != inspect.Parameter.empty else ""
            is_numeric = param.annotation in (float, int)
            element = html.Div([
                html.Label(f"{formatted_label}:", className="small fw-semibold mt-2"),
                dcc.Input(
                    type="number" if is_numeric else "text",
                    value=default_val,
                    id={'type': 'dynamic-input', 'name': param_name},
                    className="form-control form-control-sm"
                )
            ])
        ui_elements.append(element)
    return ui_elements


# PIPELINE 3: Dynamic Real-time Calculations Latency Estimation Matching
@app.callback(
    Output('runtime-estimation-badge', 'children'),
    Input('tool-selector', 'value'),
    Input({'type': 'dynamic-input', 'name': ALL}, 'value'),
    State({'type': 'dynamic-input', 'name': ALL}, 'id')
)
def determine_runtime_estimation(tool_name, input_values, input_ids):
    if not tool_name or tool_name not in TOOL_REGISTRY: 
        return ""
        
    func = TOOL_REGISTRY[tool_name]
    if not hasattr(func, 'estimated_times'):
        return dbc.Badge("⏱️ Est. Runtime: Variable / Instant", color="secondary", className="p-2 w-100")
        
    signature = inspect.signature(func)
    param_order = list(signature.parameters.keys())
    current_inputs = {id_dict['name']: val for val, id_dict in zip(input_values, input_ids)}
    
    try:
        # Convert user's active configuration array into an index matching tuple keys
        # Floats entered via inputs are handled safely
        user_combination = tuple(
            float(current_inputs[p]) if type(current_inputs[p]) in (int, float) else current_inputs[p]
            for p in param_order if p in current_inputs
        )
        
        if user_combination in func.estimated_times:
            est_duration = func.estimated_times[user_combination]
            is_heavy = "seconds" in est_duration and any(int(s) > 4 for s in est_duration.split() if s.isdigit())
            return dbc.Badge(f"⏱️ Est. Runtime: {est_duration}", color="warning" if is_heavy else "info", className="p-2 w-100 fs-6")
    except KeyError:
        return ""
        
    return dbc.Badge("⏱️ Est. Runtime: Custom Configuration Variable", color="light", className="text-dark p-2 w-100")


# PIPELINE 4: Run Core Analytics Modules & Map Framework Structures
@app.callback(
    Output('text-summary-box', 'children'),
    Output('text-summary-box', 'style'),
    Output('main-chart-display', 'figure'),
    Output('main-chart-display', style),
    Output('table-display-container', 'children'),
    Output('export-panel', style),
    Input('run-btn', 'n_clicks'),
    State('tool-selector', 'value'),
    State({'type': 'dynamic-input', 'name': ALL}, 'value'),
    State({'type': 'dynamic-input', 'name': ALL}, 'id'),
    prevent_initial_call=True
)
def run_analytics_execution_engine(n_clicks, tool_name, input_values, input_ids):
    global CURRENT_DF, CURRENT_FIG, CURRENT_META
    if not n_clicks: 
        return "", {"display": "none"}, dash.no_update, {"display": "none"}, "", {"display": "none"}
        
    func = TOOL_REGISTRY[tool_name]
    kwargs = {id_dict['name']: val for val, id_dict in zip(input_values, input_ids)}
    
    # Run calculation module
    results = func(**kwargs)
    
    # Store matrix items into globally cached space fields for export utilities
    CURRENT_DF = results['dataframe']
    CURRENT_FIG = results['figure']
    CURRENT_META = {"tool_name": tool_name, "arguments": kwargs}
    
    table_preview = dbc.Table.from_dataframe(CURRENT_DF, striped=True, bordered=True, hover=True, responsive=True, size="sm")
    
    return (
        results['summary_text'], 
        {"display": "block"}, 
        CURRENT_FIG, 
        {"display": "block"}, 
        table_preview, 
        {"display": "block"}
    )


# PIPELINE 5: Process Multi-channel File Exports (CSV / Interactive HTML / Audit Reports)
@app.callback(
    Output("download-csv", "data"),
    Output("download-html-fig", "data"),
    Output("download-report", "data"),
    Input("btn-csv", "n_clicks"),
    Input("btn-chart", "n_clicks"),
    Input("btn-report", "n_clicks"),
    State("url", "href"),
    prevent_initial_call=True
)
def routing_export_download_channels(n_csv, n_chart, n_report, current_url):
    trigger_id = ctx.triggered_id
    
    if trigger_id == "btn-csv" and CURRENT_DF is not None:
        return dcc.send_dataframe(CURRENT_DF.to_csv, "exported_metrics_data.csv", index=False), dash.no_update, dash.no_update
        
    elif trigger_id == "btn-chart" and CURRENT_FIG is not None:
        html_string = pio.to_html(CURRENT_FIG, full_html=True)
        return dash.no_update, dcc.send_string(html_string, "interactive_chart_frame.html"), dash.no_update
        
    elif trigger_id == "btn-report" and CURRENT_META:
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        param_lines = "\n".join([f"- **{k}**: {v}" for k, v in CURRENT_META['arguments'].items()])
        
        markdown_template = f"""# Analytical Systems Logging & Audit Report
---
## 📋 Execution Information Metadata
- **Active Engine Module Analyzed:** {CURRENT_META['tool_name']}
- **Timestamp Logged:** {timestamp_str}
- **Direct System Dashboard State Link:** [{current_url}]({current_url})

## ⚙️ Core Variables Array Input Context
{param_lines}

## 📊 Evaluation Summary Output Conclusions
Data array matrices were fully mapped via algorithmic parsing structures. Download accompanying spreadsheet or HTML chart wrappers for deeper diagnostics.
"""
        return dash.no_update, dash.no_update, dcc.send_string(markdown_template, "audit_analytics_report.md")

    return dash.no_update, dash.no_update, dash.no_update


# ---------------------------------------------------------------------
# RUN APPLICATION SYSTEM
# ---------------------------------------------------------------------
if __name__ == '__main__':
    # Make sure you have dash and dash_bootstrap_components installed in your terminal environment:
    # pip install dash dash-bootstrap-components pandas plotly
    app.run_server(debug=True)



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
  
import pandas as pd
import plotly.express as px
import time

def run_heavy_calculation(sensor_id: ['Sensor_A', 'Sensor_B'], complexity: ['Simple', 'Deep Learning']):
    """Performs complex algorithmic modeling on hardware streams."""
    # Simulation of variable runtime
    if complexity == 'Deep Learning':
        time.sleep(5) 
    else:
        time.sleep(1)
        
    df = pd.DataFrame({'X': [1, 2, 3], 'Y': [4, 5, 6]})
    fig = px.line(df, x='X', y='Y', title="Analysis Complete")
    
    return {"dataframe": df, "figure": fig, "summary_text": "Completed successfully."}

# --- THE ESTIMATION MAP ---
# Keys are tuples representing the matching argument values in order of the function signature
run_heavy_calculation.estimated_times = {
    ('Sensor_A', 'Simple'): "1-2 seconds",
    ('Sensor_A', 'Deep Learning'): "5-10 seconds",
    ('Sensor_B', 'Simple'): "2-3 seconds",
    ('Sensor_B', 'Deep Learning'): "12-15 seconds",
}
