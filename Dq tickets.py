import pandas as pd
import plotly.express as px
import plotly.graph_objects as px_go
from plotly.subplots import make_subplots

# -------------------------------------------------------------------
# CONFIGURATION / DICTIONARY SETUP
# -------------------------------------------------------------------
# Define rules for each column:
# - mandatory: bool (True if required, False if optional)
# - ignore: bool (True to skip column entirely from QA calculations)
# - min_length: int (Minimum character length expected)
# - max_length: int (Maximum character length expected)

COLUMN_RULES = {
    "TicketID": {"mandatory": True, "ignore": False, "min_length": 3, "max_length": 10},
    "Title": {"mandatory": True, "ignore": False, "min_length": 10, "max_length": 100},
    "Description": {"mandatory": True, "ignore": False, "min_length": 20, "max_length": 2000},
    "Status": {"mandatory": True, "ignore": False, "min_length": 3, "max_length": 20},
    "Assignee": {"mandatory": False, "ignore": False, "min_length": 2, "max_length": 50},
    "Priority": {"mandatory": False, "ignore": False, "min_length": 3, "max_length": 10},
    "InternalSystemNotes": {"mandatory": False, "ignore": True, "min_length": 0, "max_length": 5000},
}

def analyze_devops_csv(csv_path: str, rules: dict):
    df = pd.read_csv(csv_path)
    
    # Filter active columns (excluding ignored ones)
    active_cols = [col for col in df.columns if col in rules and not rules[col].get("ignore", False)]
    
    # Dataframes to track quality metrics
    validity_matrix = pd.DataFrame(index=df.index)
    
    column_stats = []
    
    for col in active_cols:
        col_rule = rules[col]
        is_mandatory = col_rule.get("mandatory", False)
        min_len = col_rule.get("min_length", 0)
        max_len = col_rule.get("max_length", float("inf"))
        
        # Check populated state
        is_populated = df[col].notna() & (df[col].astype(str).str.strip() != "")
        
        # Check string length range
        str_lengths = df[col].astype(str).str.len()
        valid_length = (str_lengths >= min_len) & (str_lengths <= max_len)
        
        # Determine cell validity
        if is_mandatory:
            cell_valid = is_populated & valid_length
        else:
            # If optional, valid if empty OR (if populated, meets length)
            cell_valid = (~is_populated) | (is_populated & valid_length)
            
        validity_matrix[col] = cell_valid
        
        # Column level aggregations
        column_stats.append({
            "Column": col,
            "Mandatory": is_mandatory,
            "Populated Rate (%)": round((is_populated.sum() / len(df)) * 100, 2),
            "Length Violation Count": (~valid_length & is_populated).sum(),
            "Quality Score (%)": round((cell_valid.sum() / len(df)) * 100, 2)
        })

    # Ticket (Row) level Quality Calculation
    ticket_scores = (validity_matrix.sum(axis=1) / len(active_cols)) * 100
    df["Ticket_QA_Score"] = round(ticket_scores, 2)
    
    col_summary_df = pd.DataFrame(column_stats)
    return df, col_summary_df, active_cols

def generate_interactive_report(df, col_summary_df, output_html="devops_qa_report.html"):
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Column Quality Scores (%)", 
            "Ticket Quality Score Distribution", 
            "Column Populated Rate vs Length Violations",
            "Lowest Quality Tickets (Top 10)"
        ),
        specs=[[{"type": "bar"}, {"type": "histogram"}],
               [{"type": "bar"}, {"type": "table"}]]
    )
    
    # Chart 1: Column Quality Score
    fig.add_trace(
        px_go.Bar(
            x=col_summary_df["Column"], 
            y=col_summary_df["Quality Score (%)"],
            marker_color="teal",
            name="Quality Score"
        ),
        row=1, col=1
    )
    
    # Chart 2: Ticket Score Distribution
    fig.add_trace(
        px_go.Histogram(
            x=df["Ticket_QA_Score"],
            nbinsx=10,
            marker_color="indigo",
            name="Tickets"
        ),
        row=1, col=2
    )

    # Chart 3: Populated Rate
    fig.add_trace(
        px_go.Bar(
            x=col_summary_df["Column"], 
            y=col_summary_df["Populated Rate (%)"],
            marker_color="coral",
            name="Populated Rate"
        ),
        row=2, col=1
    )

    # Chart 4: Table of lowest quality tickets
    worst_tickets = df.sort_values(by="Ticket_QA_Score").head(10)
    display_cols = [c for c in ["TicketID", "Title", "Ticket_QA_Score"] if c in df.columns]
    
    fig.add_trace(
        px_go.Table(
            header=dict(values=display_cols, fill_color="paleturquoise", align="left"),
            cells=dict(values=[worst_tickets[k] for k in display_cols], fill_color="lavender", align="left")
        ),
        row=2, col=2
    )

    fig.update_layout(
        title_text="DevOps CSV Data Quality Analysis Dashboard",
        height=800,
        showlegend=False
    )
    
    fig.write_html(output_html)
    print(f"Report successfully saved to {output_html}")

# -------------------------------------------------------------------
# EXECUTION EXAMPLE
# -------------------------------------------------------------------
if __name__ == "__main__":
    # Load your CSV here:
    csv_filename = "devops_tickets.csv"
    
    # 1. Process data
    df_analyzed, col_summary, active_cols = analyze_devops_csv(csv_filename, COLUMN_RULES)
    
    # 2. Render HTML Report
    generate_interactive_report(df_analyzed, col_summary)



Dictionary Config (COLUMN_RULES): Set mandatory, ignore, min_length, and max_length per column.
Column-Level Analysis: Measures population rate, string length compliance, and overall column quality score.
Ticket-Level Analysis: Calculates an overall quality percentage for each ticket row based on active columns.
Standalone Interactive HTML: Generates a self-contained dashboard with Plotly charts and a low-quality ticket visualizer table.
