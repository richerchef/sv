import dash
from dash import dcc, html, Input, Output, State, dash_table
import plotly.express as px
import pandas as pd
import io

# Initialize Dash 1.19.0
app = dash.Dash(__name__)

# --- STEP 1: LAYOUT DEFINITION ---
# This describes what the user sees on the screen.
app.layout = html.Div([
    html.H1("Data Science Tool: Extraction & Analysis", style={'textAlign': 'center'}),
    html.Hr(),

    html.Div([
        # OPTION 1: Platform Selection
        html.Label("1. Select Platform:"),
        dcc.Dropdown(
            id='platform-dropdown',
            options=[{'label': i, 'value': i} for i in ['Alpha', 'Beta', 'Gamma']],
            value='Alpha'
        ),
        html.Br(),

        # OPTION 2 & 3: Date Range
        html.Label("2. Date Range:"),
        html.Div([
            dcc.Input(id='date-from', type='text', value='2026-01-01', placeholder='YYYY-MM-DD'),
            html.Span(" to "),
            dcc.Input(id='date-to', type='text', value='2026-01-10', placeholder='YYYY-MM-DD'),
        ]),
        html.Br(),

        # OPTION 4: Sensor List
        html.Label("4. Sensor Type:"),
        dcc.Dropdown(
            id='sensor-dropdown',
            options=[{'label': i, 'value': i} for i in ['Temperature', 'Pressure', 'Vibration']],
            value='Temperature'
        ),
        html.Br(),

        # OPTION 5: Data Quality Toggle
        html.Label("5. Data Quality Mode:"),
        dcc.Checklist(
            id='dq-check',
            options=[{'label': 'Filter High Quality Only (>0.90)', 'value': 'HIGH'}],
            value=[]
        ),
        html.Br(),

        # THE TRIGGER BUTTON
        html.Button('RUN ANALYSIS', id='run-button', n_clicks=0, 
                    style={'width': '100%', 'height': '50px', 'backgroundColor': '#007BFF', 'color': 'white'})
    ], style={'width': '25%', 'display': 'inline-block', 'padding': '20px', 'backgroundColor': '#f9f9f9'}),

    # OUTPUT SECTION
    html.Div([
        html.Div(id='status-area', style={'fontWeight': 'bold', 'color': 'blue'}),
        dcc.Graph(id='results-graph'),
        html.H3("Data Preview"),
        dash_table.DataTable(
            id='results-table',
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'}
        ),
        html.Br(),
        # Simple Report Button (Triggers browser print for now)
        html.Button("GENERATE PDF REPORT", id="print-btn", n_clicks=0)
    ], style={'width': '70%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px'})
])

# --- STEP 2: THE BRAIN (CALLBACKS) ---
# This is where the logic happens when the button is clicked.
@app.callback(
    [Output('results-graph', 'figure'),
     Output('results-table', 'data'),
     Output('status-area', 'children')],
    [Input('run-button', 'n_clicks')],
    [State('platform-dropdown', 'value'),
     State('date-from', 'value'),
     State('date-to', 'value'),
     State('sensor-dropdown', 'value'),
     State('dq-check', 'value')]
)
def update_output(n_clicks, plat, d_from, d_to, sens, dq):
    # Prevent logic from running automatically on page load
    if n_clicks == 0:
        return {}, [], "Awaiting instructions..."

    # --- DATA GET (Swappable for SQLAlchemy) ---
    # Logic: Read CSV and filter based on dropdowns
    df = pd.read_csv('mock_data.csv')
    
    # Simple filtering logic
    filtered_df = df[
        (df['platform'] == plat) & 
        (df['sensor'] == sens)
    ].copy()

    # --- DATA QUALITY LOGIC ---
    # If the user checked the DQ option, filter further
    if 'HIGH' in dq:
        filtered_df = filtered_df[filtered_df['quality_score'] > 0.90]

    # --- PYTHON MANIPULATION ---
    # Here you can add your custom analysis (Rolling means, outlier detection, etc.)
    filtered_df['rolling_val'] = filtered_df['value'].rolling(window=2, min_periods=1).mean()

    # --- VISUALIZATION ---
    fig = px.line(filtered_df, x='date', y='value', 
                  title=f"Report: {plat} - {sens}",
                  template="plotly_white")
    
    # Add dots to the line
    fig.update_traces(mode='lines+markers')

    status = f"Analysis Complete. Found {len(filtered_df)} rows for {plat}."
    
    return fig, filtered_df.to_dict('records'), status

# --- STEP 3: SIMPLE REPORTING TOOL ---
# This uses a client-side "window.print()" to create a PDF of the current view.
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks > 0) {
            window.print();
        }
        return null;
    }
    """,
    Output('print-btn', 'data-dummy'), # Dummy output
    Input('print-btn', 'n_clicks')
)

if __name__ == '__main__':
    app.run_server(debug=True)
