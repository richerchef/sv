import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. Configuration & Data Loading
# ==========================================
# Replace 'your_devops_file.csv' with the actual path to your CSV file
csv_filename = 'your_devops_file.csv' 
target_year = 2026  # Change to the year you want to evaluate

# Define your annual target numbers for each Area
targets = {
    'Area A': 200,
    'Area B': 300,
    'Area C': 100
}

# Load the CSV data
df = pd.read_csv(csv_filename)

# Ensure the columns match your CSV exactly (case-sensitive)
# Standardizing column names to match your schema
date_col = 'Closed Date'
area_col = 'Area'

# Convert the closed date to datetime and filter for the evaluation year
df[date_col] = pd.to_datetime(df[date_col])
df = df[df[date_col].dt.year == target_year]

# ==========================================
# 2. Data Aggregation & Processing
# ==========================================
# Create a full 12-month sequence from January to December to avoid missing gaps
all_months = pd.period_range(start=f'{target_year}-01', end=f'{target_year}-12', freq='M')

# Group by Area and Month to count items closed
df['Month'] = df[date_col].dt.to_period('M')
monthly_counts = df.groupby([area_col, 'Month']).size().unstack(fill_value=0)

# Reindex to ensure all 12 calendar months exist for every area
monthly_counts = monthly_counts.reindex(columns=all_months, fill_value=0)

# Compute running cumulative closures over the course of the year
cumulative_actual = monthly_counts.cumsum(axis=1)

# Format month names for the X-axis labels ('Jan', 'Feb', etc.)
month_labels = [m.strftime('%b') for m in all_months]

# ==========================================
# 3. Chart Generation
# ==========================================

# --- APPROACH 1: Cumulative Burn-Up Charts (Subplots per Area) ---
fig1, axes = plt.subplots(len(targets), 1, figsize=(10, 3 * len(targets)), sharex=True, gridspec_kw={'hspace': 0.4})
if len(targets) == 1:
    axes = [axes]

for i, area in enumerate(targets.keys()):
    ax = axes[i]
    annual_target = targets[area]
    
    # Linear expected target path line from 0 up to the annual target
    target_line = np.linspace(0, annual_target, 13)[1:]
    
    # Extract actuals or default to 0 if the area doesn't appear in the dataset
    actual_line = cumulative_actual.loc[area].values if area in cumulative_actual.index else np.zeros(12)
        
    # Plot expected vs actual paths
    ax.plot(month_labels, target_line, label='Expected Target Path', color='darkgray', linestyle='--')
    ax.plot(month_labels, actual_line, label='Actual Cumulative Closures', color='royalblue', marker='o', linewidth=2)
    
    # Fill background color dynamically based on whether actuals exceed expectations
    ax.fill_between(month_labels, actual_line, target_line, 
                    where=(actual_line >= target_line), 
                    interpolate=True, color='green', alpha=0.15, label='Ahead of Target')
    ax.fill_between(month_labels, actual_line, target_line, 
                    where=(actual_line < target_line), 
                    interpolate=True, color='red', alpha=0.15, label='Behind Target')
    
    ax.set_title(f'{area} Progress (Yearly Target: {annual_target})', fontsize=12, fontweight='bold')
    ax.set_ylabel('Closures')
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', fontsize=9)

axes[-1].set_xlabel('Month')
fig1.savefig('cumulative_burnup_chart.png', bbox_inches='tight')


# --- APPROACH 2: Consolidated Net Variance Chart (All Areas in One) ---
fig2, ax2 = plt.subplots(figsize=(11, 6))
ax2.axhline(0, color='black', linestyle='-', linewidth=1.5, label='On Target Baseline')

for area, annual_target in targets.items():
    target_line = np.linspace(0, annual_target, 13)[1:]
    actual_line = cumulative_actual.loc[area].values if area in cumulative_actual.index else np.zeros(12)
    
    # Compute deviation from the expectation line
    variance = actual_line - target_line
    ax2.plot(month_labels, variance, label=f'{area} (Target: {annual_target})', marker='o', linewidth=2)

# Subtle shading background to differentiate positive and negative variance zones
ax2.fill_between(month_labels, 0, 1, where=np.ones(12, dtype=bool), color='green', alpha=0.03, transform=ax2.get_yaxis_transform())
ax2.fill_between(month_labels, -1, 0, where=np.ones(12, dtype=bool), color='red', alpha=0.03, transform=ax2.get_yaxis_transform())

ax2.set_title(f'Net Variance from Expected Target Path ({target_year})', fontsize=14, fontweight='bold')
ax2.set_xlabel('Month')
ax2.set_ylabel('Items Ahead (+) / Behind (-) Target')
ax2.grid(True, linestyle=':', alpha=0.6)
ax2.legend(loc='upper left')

fig2.savefig('variance_from_target_chart.png', bbox_inches='tight')

print("Charts successfully saved as 'cumulative_burnup_chart.png' and 'variance_from_target_chart.png'")
