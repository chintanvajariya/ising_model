import numpy as np
from scipy.ndimage import convolve
from numba import njit

class IsingSim:
    def __init__(self, 
                 N=25, 
                 T=2.5, 
                 J_intra=2.5, 
                 J_inter=0.25, 
                 trials=1000,
                 external_field_range=(-2, 2),
                 seed=None):

        self.N = N
        self.T = T
        self.J_intra = J_intra
        self.J_inter = J_inter
        self.trials = trials
        self.external_field_range = external_field_range
        self.random = np.random.default_rng(seed)

        # Create lattice and factions
        self.lattice = self.random.choice([-1, 1], size=(N, N))
        self.num_factions = self._determine_num_factions()
        self.faction_map = self._assign_factions()
        self.h_values = self._generate_h_values()
        self.h_map = self._generate_h_map()

        # Time tracking
        self.current_trial = 0
        self.energies = [self._get_total_energy()]

        # Snapshots for rewinding
        self.snapshots = []

    def _determine_num_factions(self):
        return min(12, max(3, self.N // 5 + 2))

    def _assign_factions(self):
        faction_map = -1 * np.ones((self.N, self.N), dtype=int)
        visited = np.zeros((self.N, self.N), dtype=bool)
        frontier = []

        centers = self.random.choice(self.N * self.N, size=self.num_factions, replace=False)
        centers = np.column_stack(np.unravel_index(centers, (self.N, self.N)))

        for faction_id, (r, c) in enumerate(centers):
            faction_map[r, c] = faction_id
            visited[r, c] = True
            frontier.append((r, c, faction_id))

        while frontier:
            r, c, faction_id = frontier.pop(0)
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < self.N and 0 <= nc < self.N):
                    continue
                if not visited[nr, nc]:
                    faction_map[nr, nc] = faction_id
                    visited[nr, nc] = True
                    frontier.append((nr, nc, faction_id))

        return faction_map

    def _generate_h_values(self):
        h_vals = []
        while len(h_vals) < self.num_factions:
            val = round(self.random.uniform(*self.external_field_range), 2)
            if abs(val) >= 0.1:
                h_vals.append(val)
        return h_vals

    def _generate_h_map(self):
        h_map = np.zeros_like(self.faction_map, dtype=float)
        unique_factions = np.unique(self.faction_map)
        for i, faction in enumerate(unique_factions):
            h_map[self.faction_map == faction] = self.h_values[i]
        return h_map

    @staticmethod
    @njit
    def _get_energy_faction(row, col, flip, lattice, faction_map, h_map, J_intra, J_inter):
        N = lattice.shape[0]
        spin = lattice[row, col] * flip
        neighbors = [
            ((row + 1) % N, col),
            ((row - 1) % N, col),
            (row, (col + 1) % N),
            (row, (col - 1) % N)
        ]
        energy = 0.0
        for r, c in neighbors:
            J = J_intra if faction_map[row, col] == faction_map[r, c] else J_inter
            energy += -J * spin * lattice[r, c]
        energy += -h_map[row, col] * spin
        return energy

    def _flip_probability(self, row, col):
        delta = (self._get_energy_faction(row, col, -1, self.lattice, self.faction_map, self.h_map, self.J_intra, self.J_inter) -
                 self._get_energy_faction(row, col,  1, self.lattice, self.faction_map, self.h_map, self.J_intra, self.J_inter))
        if delta <= 0:
            return 1.0
        else:
            return np.exp(-delta / self.T)

    def _get_total_energy(self):
        total = 0
        for row in range(self.N):
            for col in range(self.N):
                total += self._get_energy_faction(row, col, 1, self.lattice, self.faction_map, self.h_map, self.J_intra, self.J_inter)
        return total

    def step(self, num_steps=1, record_snapshots=False):
        for _ in range(num_steps):
            row, col = self.random.integers(0, self.N, size=2)
            prob = self._flip_probability(row, col)
            if self.random.random() <= prob:
                delta = (self._get_energy_faction(row, col, -1, self.lattice, self.faction_map, self.h_map, self.J_intra, self.J_inter) -
                         self._get_energy_faction(row, col,  1, self.lattice, self.faction_map, self.h_map, self.J_intra, self.J_inter))
                self.lattice[row, col] *= -1
                self.energies.append(self.energies[-1] + delta)
            else:
                self.energies.append(self.energies[-1])

            self.current_trial += 1

            if record_snapshots and (self.current_trial % 10 == 0):
                self.save_snapshot()
            
            if hasattr(self, "_decay_schedule") and self._decay_schedule:
                event = self._decay_schedule.pop(0)
                if event[0] == "field":
                    self.h_map -= event[1]
                    self.h_values = [np.mean(self.h_map[self.faction_map == f]) for f in range(self.num_factions)]


    def save_snapshot(self):
        snapshot = {
            'trial': self.current_trial,
            'lattice': self.lattice.copy(),
            'energies': np.array(self.energies),
            'h_map': self.h_map.copy()
        }
        self.snapshots.append(snapshot)

    def restore_snapshot(self, idx):
        snap = self.snapshots[idx]
        self.current_trial = snap['trial']
        self.lattice = snap['lattice'].copy()
        self.energies = list(snap['energies'])
        self.h_map = snap['h_map'].copy()

    def inject_event(self, value):
        N = self.N
        new_lattice = self.lattice.copy()
        beta = 2

        for r in range(N):
            for c in range(N):
                spin = self.lattice[r, c]
                group = self.faction_map[r, c]
                h = self.h_map[group]

                align_push = value * h * (-spin)
                h_eff = value
                local_field = h_eff + self.h_map
                aligned = self.lattice * local_field

                prob_flip = 1 / (1 + np.exp(aligned * beta))  # sigmoid-based flip prob

                rand_vals = np.random.rand(*self.lattice.shape)
                flip_mask = rand_vals < prob_flip
                self.lattice[flip_mask] *= -1


                rand_vals = np.random.rand(*prob_flip.shape)
                flip_mask = rand_vals < prob_flip
                self.lattice[flip_mask] *= -1

        self.lattice = new_lattice
        self.current_trial += 1

    def adjust_constants(self, faction_id=None, new_J_intra=None, new_J_inter=None, new_T=None, new_h=None):
        if new_J_intra is not None:
            self.J_intra = new_J_intra
        if new_J_inter is not None:
            self.J_inter = new_J_inter
        if new_T is not None:
            self.T = new_T
        if faction_id is not None and new_h is not None:
            self.h_values[faction_id] = new_h
            self.h_map[self.faction_map == faction_id] = new_h


    def get_current_state(self):
        return {
            'lattice': self.lattice.copy(),
            'faction_map': self.faction_map.copy(),
            'h_map': self.h_map.copy(),
            'energies': np.array(self.energies),
            'current_trial': self.current_trial,
        }

    def get_spin_percentages(self):
        faction_ids = np.unique(self.faction_map)
        spin_percentages = []
        for f in faction_ids:
            mask = self.faction_map == f
            total = np.sum(mask)
            if total == 0:
                spin_percentages.append(0)
            else:
                net_spin = np.sum(self.lattice[mask])
                percent = round(100 * net_spin / total, 2)
                spin_percentages.append(percent)
        return spin_percentages
    
    def get_magnetization(self):
        return np.mean(self.lattice)

    def get_agreement_score(self):
        aligned = 0
        for r in range(self.N):
            for c in range(self.N):
                spin = self.lattice[r, c]
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = (r+dr)%self.N, (c+dc)%self.N
                    aligned += (self.lattice[nr,nc] == spin)
        return aligned / (self.N * self.N * 4)
