import numpy as np

def get_spin_percentages(lattice, faction_map):
    faction_ids = np.unique(faction_map)
    spin_percentages = []
    for f in faction_ids:
        mask = faction_map == f
        total = np.sum(mask)
        if total == 0:
            spin_percentages.append(0)
        else:
            net_spin = np.sum(lattice[mask])
            percent = round(100 * net_spin / total, 2)
            spin_percentages.append(percent)
    return spin_percentages

def get_magnetization(lattice):
    return np.mean(lattice)

def get_agreement_score(lattice, N):
    aligned = 0
    for r in range(N):
        for c in range(N):
            spin = lattice[r, c]
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = (r+dr)%N, (c+dc)%N
                aligned += (lattice[nr,nc] == spin)
    return aligned / (N * N * 4)

class StateManager:
    def __init__(self):
        self.snapshots = []

    def save_snapshot(self, trial, lattice, energies, h_map):
        snapshot = {
            'trial': trial,
            'lattice': lattice.copy(),
            'energies': np.array(energies),
            'h_map': h_map.copy()
        }
        self.snapshots.append(snapshot)

    def restore_snapshot(self, idx):
        return self.snapshots[idx] 