import plotly.graph_objects as go
import plotly.io as pio
import plotly.express as px
import pandas as pd
import numpy as np

def apply_corporate_template():
    """
    Defines and registers the corporate Plotly template.
    """
    # 1. Define your brand palette
    brand_primary = '#1A237E'  # Deep Blue
    brand_colors = [brand_primary, '#5C6BC0', '#9FA8DA', '#E8EAF6', '#FFD700', '#00BFA5']

    # 2. Build the template
    corp_template = go.layout.Template(
        layout=go.Layout(
            # Global sequence for multi-category charts
            colorway=brand_colors,
            
            # Formatting
            font=dict(family="Arial, sans-serif", size=12, color="#333333"),
            paper_bgcolor='white',
            plot_bgcolor='#FBFBFB',
            
            # Clean Axes
            xaxis=dict(gridcolor='white', linecolor='#D1D1D1', ticks='outside'),
            yaxis=dict(gridcolor='white', linecolor='#D1D1D1', ticks='outside'),
            
            # Legend positioning
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        ),
        # 3. Specific defaults for single-trace charts (The MVP Fix)
        data=dict(
            bar=[go.Bar(marker_color=brand_primary)],
            scatter=[go.Scatter(line=dict(color=brand_primary, width=3), marker=dict(color=brand_primary))],
            line=[go.Scatter(line=dict(color=brand_primary, width=3))]
        )
    )

    # Register and Set Default
    pio.templates["corp_mvp"] = corp_template
    pio.templates.default = "corp_mvp"
    print("Corporate Template Applied Successfully.")

def generate_test_charts():
    """
    Creates mocked-up charts to verify the template.
    """
    # Mock Data
    df = pd.DataFrame({
        "Category": ["A", "B", "C", "D"],
        "Values": [45, 70, 55, 85],
        "Group": ["Team 1", "Team 1", "Team 2", "Team 2"],
        "Timeline": pd.date_range(start="2023-01-01", periods=4, freq="ME")
    })

    print("Generating test charts...")

    # 1. Single Bar Chart (Tests the 'data' default)
    fig1 = px.bar(df, x="Category", y="Values", title="Standard Bar Chart (Single Color)")
    fig1.show()

    # 2. Stacked Bar Chart (Tests the 'colorway')
    fig2 = px.bar(df, x="Group", y="Values", color="Category", title="Stacked Bar Chart (Colorway)")
    fig2.show()

    # 3. Line Chart (Tests line width and brand color)
    fig3 = px.line(df, x="Timeline", y="Values", title="Corporate Line Chart")
    fig3.show()

    # 4. Scatter Plot (Tests markers)
    fig4 = px.scatter(df, x="Values", y="Values", size="Values", color="Category", title="Corporate Scatter Plot")
    fig4.show()

if __name__ == "__main__":
    # Run the setup
    apply_corporate_template()
    
    # Run the tests
    generate_test_charts()
