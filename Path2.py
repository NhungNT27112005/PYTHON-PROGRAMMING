import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "_", str(name))

df = pd.read_csv('results.csv')

numeric_cols = df.select_dtypes(include='number').columns

with open('top_3.txt', 'w', encoding='utf-8') as f:
    for col in numeric_cols:
        f.write(f"\n=== {col} ===\n")
        top3 = df.nlargest(3, col)[['Player', col]]
        f.write("Top 3 players:\n")
        f.write(top3.to_string(index=False))
        f.write("\n")
        bottom3 = df.nsmallest(3, col)[['Player', col]]
        f.write("Bottom 3 players:\n")
        f.write(bottom3.to_string(index=False))
        f.write("\n")

median_row = df[numeric_cols].median()
mean_row = df[numeric_cols].mean()
std_row = df[numeric_cols].std()

overall_df = pd.DataFrame([median_row, mean_row, std_row])
overall_df.insert(0, 'Statistic', ['Median', 'Mean', 'Std'])

team_stats = []
for team, group in df.groupby('Team'):
    median = group[numeric_cols].median()
    mean = group[numeric_cols].mean()
    std = group[numeric_cols].std()
    team_stats.append([team, 'Median'] + list(median))
    team_stats.append([team, 'Mean'] + list(mean))
    team_stats.append([team, 'Std'] + list(std))

team_df = pd.DataFrame(team_stats, columns=['Team', 'Statistic'] + list(numeric_cols))

overall_df.to_csv('results2.csv', index=False)
team_df.to_csv('results2.csv', mode='a', index=False)


os.makedirs('histograms/league', exist_ok=True)
os.makedirs('histograms/teams', exist_ok=True)

# League-wide histograms
for col in numeric_cols:
    if df[col].isna().all():
        continue
    plt.figure(figsize=(8, 6))
    plt.hist(df[col].dropna(), bins=20, edgecolor='black')
    plt.title(f'Distribution of {col} (All Players)')
    plt.xlabel(col)
    plt.ylabel('Frequency')
    safe_col = sanitize_filename(col)
    path = f'histograms/league/{safe_col}_league.png'
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"[✓] Created league charts for statistics: {col}")

# Team-specific histograms
for team in df['Team'].unique():
    team_data = df[df['Team'] == team]
    safe_team = sanitize_filename(team)
    team_dir = f'histograms/teams/{safe_team}'
    os.makedirs(team_dir, exist_ok=True)
    for col in numeric_cols:
        if team_data[col].isna().all():
            continue
        plt.figure(figsize=(8, 6))
        plt.hist(team_data[col].dropna(), bins=20, edgecolor='black')
        plt.title(f'Distribution of {col} ({team})')
        plt.xlabel(col)
        plt.ylabel('Frequency')
        safe_col = sanitize_filename(col)
        file_path = f'{team_dir}/{safe_col}.png'
        plt.savefig(file_path, bbox_inches='tight')
        plt.close()
    print(f"[✓] Created a chart for the team: {team}")

team_sums = df.groupby('Team')[numeric_cols].sum()
highest_score_teams = {}
for col in numeric_cols:
    if team_sums[col].isna().all():
        continue
    max_team = team_sums[col].idxmax()
    highest_score_teams[col] = max_team

team_counts = pd.Series(highest_score_teams.values()).value_counts()

print("\nTeams with highest scores for each statistic:")
for col, team in highest_score_teams.items():
    print(f"{col}: {team}")

best_team = team_counts.idxmax()
best_team_count = team_counts.max()
print(f"\nBest-performing team: {best_team} (highest in {best_team_count} statistics)")
