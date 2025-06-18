import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.impute import SimpleImputer 

# Load the provided results.csv data
data = pd.read_csv('results.csv')

# Define numeric columns (exclude non-numeric: Player, Nation, Team, Position)
non_numeric_cols = ['Player', 'Nation', 'Team', 'Position']
numeric_cols = [col for col in data.columns if col not in non_numeric_cols]

# Convert "N/a" to NaN and ensure numeric columns are float
for col in numeric_cols:
    data[col] = pd.to_numeric(data[col], errors='coerce')

# Preprocess data: Impute NaN with median and standardize
X = data[numeric_cols].copy()

imputer = SimpleImputer(strategy='median')
X_imputed = imputer.fit_transform(X)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_imputed)  

# 1. Determine optimal number of clusters using elbow method and silhouette score
inertias = []
silhouette_scores = []
k_range = range(2, 11)  

for k in k_range:
    try:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled) 
        inertias.append(kmeans.inertia_)
        score = silhouette_score(X_scaled, kmeans.labels_)
        silhouette_scores.append(score)
    except Exception as e:
        print(f"Error with k={k}: {str(e)}")
        inertias.append(np.nan)
        silhouette_scores.append(np.nan)

# Plot elbow curve
plt.figure(figsize=(8, 6))
plt.plot(k_range, inertias, 'bo-')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Inertia')
plt.title('Elbow Method for Optimal k')
plt.grid(True)
plt.savefig('elbow_plot.png', bbox_inches='tight')
plt.show()
plt.close()

# Plot silhouette scores
plt.figure(figsize=(8, 6))
plt.plot(k_range, silhouette_scores, 'ro-') 
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Silhouette Score')
plt.title('Silhouette Score for Different k')
plt.grid(True)
plt.savefig('silhouette_plot.png', bbox_inches='tight')
plt.show()
plt.close()


optimal_k = 3
print(f"Chosen number of clusters: {optimal_k}")

# 2. Apply K-means with optimal k
kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
clusters = kmeans.fit_predict(X_scaled)
data['Cluster'] = clusters

# Save clustered data for inspection
data[['Player', 'Nation', 'Team', 'Position', 'Cluster']].to_csv('clustered_players.csv', index=False)
print("Clustered player data saved to 'clustered_players.csv'.")

# 3. PCA to reduce dimensions to 2D
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
explained_variance = pca.explained_variance_ratio_.sum()
print(f"Explained variance by 2 PCA components: {explained_variance:.2%}")

# 4. Plot 2D cluster scatter plot
plt.figure(figsize=(10, 8))
scatter = plt.scatter(X_pca[:, 0], X_pca[:, 1], c=clusters, cmap='viridis', s=100)
plt.colorbar(scatter, label='Cluster')
plt.xlabel('PCA Component 1')
plt.ylabel('PCA Component 2')
plt.title(f'2D PCA Cluster Plot (k={optimal_k})')

# Add player names as labels
for i, player in enumerate(data['Player']):
    plt.annotate(player, (X_pca[i, 0], X_pca[i, 1]), fontsize=8, alpha=0.7)

plt.savefig('clusters_2d.png', bbox_inches='tight')
plt.close()
print("2D PCA cluster plot saved to 'clusters_2d.png'.")

# 5. Analyze clusters
print("\nCluster Analysis:")
for cluster in range(optimal_k):
    cluster_data = data[data['Cluster'] == cluster]
    print(f"\nCluster {cluster} ({len(cluster_data)} players):")
    print("Teams:", cluster_data['Team'].value_counts().to_dict())
    print("Positions:", cluster_data['Position'].value_counts().to_dict())
    print("Sample Players:", cluster_data['Player'].head(3).tolist())
    # Key statistics (mean values)
    cluster_means = cluster_data[numeric_cols].mean()
    print("Key Stats:")
    for stat in ['Gls', 'Ast', 'Min', 'GA90', 'Save%']:
        print(f"  {stat}: {cluster_means.get(stat, np.nan):.2f}")