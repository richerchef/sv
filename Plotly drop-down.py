import plotly.graph_objects as go

def create_time_toggle_chart(df_input, title_name):
    # Ensure date is datetime
    df_input['Date'] = pd.to_datetime(df_input['Date'])
    
    # 1. Prepare aggregations
    daily = df_input.groupby(df_input['Date'].dt.date)['Username'].nunique().reset_index()
    daily.columns = ['Date', 'Users']

    # Weekly (Monday start)
    weekly = df_input.set_index('Date').resample('W-MON')['Username'].nunique().reset_index()
    weekly.columns = ['Date', 'Users']

    # Monthly (Month Start)
    monthly = df_input.set_index('Date').resample('MS')['Username'].nunique().reset_index()
    monthly.columns = ['Date', 'Users']

    # 2. Create Figure
    fig = go.Figure()

    # Add the initial Daily trace
    fig.add_trace(go.Bar(
        x=daily['Date'], 
        y=daily['Users'], 
        name="Users", 
        marker_color='#4361ee'
    ))

    # 3. Fix the Dropdown Arguments
    # Note the double brackets [[ ... ]] - this is the fix!
    fig.update_layout(
        updatemenus=[
            dict(
                type="dropdown",
                direction="down",
                x=0.01, y=1.2,
                showactive=True,
                buttons=list([
                    dict(
                        label="Daily",
                        method="update",
                        args=[
                            {"x": [daily['Date']], "y": [daily['Users']]}, # Data update
                            {"title": f"{title_name}: Daily Unique Users"} # Layout update
                        ]
                    ),
                    dict(
                        label="Weekly",
                        method="update",
                        args=[
                            {"x": [weekly['Date']], "y": [weekly['Users']]},
                            {"title": f"{title_name}: Weekly Unique Users"}
                        ]
                    ),
                    dict(
                        label="Monthly",
                        method="update",
                        args=[
                            {"x": [monthly['Date']], "y": [monthly['Users']]},
                            {"title": f"{title_name}: Monthly Unique Users"}
                        ]
                    ),
                ]),
            )
        ],
        title=f"{title_name}: Daily Unique Users",
        template="plotly_white",
        margin=dict(t=80) # Add space for the dropdown
    )
    
    return fig.to_html(full_html=False, include_plotlyjs='cdn')
  
