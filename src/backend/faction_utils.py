import numpy as np

def initialize_factions(N, num_factions, random):
    faction_map = -1 * np.ones((N, N), dtype=int)
    visited = np.zeros((N, N), dtype=bool)
    frontier = []

    # Choose random centers for each faction
    centers = random.choice(N * N, size=num_factions, replace=False)
    centers = np.column_stack(np.unravel_index(centers, (N, N)))

    # Initialize each faction from its center
    for faction_id, (r, c) in enumerate(centers):
        faction_map[r, c] = faction_id
        visited[r, c] = True
        frontier.append((r, c, faction_id))

    # Flood fill to assign remaining cells to nearest faction
    while frontier:
        r, c, faction_id = frontier.pop(0)
        for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < N and 0 <= nc < N):
                continue
            if not visited[nr, nc]:
                faction_map[nr, nc] = faction_id
                visited[nr, nc] = True
                frontier.append((nr, nc, faction_id))

    return faction_map

def generate_h_values(num_factions, external_field_range, random):
    h_vals = []
    while len(h_vals) < num_factions:
        val = round(random.uniform(*external_field_range), 2)
        if abs(val) >= 0.1:
            h_vals.append(val)
    return h_vals

def generate_h_map(faction_map, h_values):
    h_map = np.zeros_like(faction_map, dtype=float)
    unique_factions = np.unique(faction_map)
    for i, faction in enumerate(unique_factions):
        h_map[faction_map == faction] = h_values[i]
    return h_map 