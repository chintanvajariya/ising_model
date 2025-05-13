import numpy as np
from .faction_utils import initialize_factions, generate_h_values, generate_h_map
from .energy_utils import get_energy_faction, get_total_energy
from .state_utils import get_spin_percentages, get_magnetization, get_agreement_score

class IsingSim:
    def __init__(self, 
                 N=25, 
                 T=2.5, 
                 J_intra=2.5, 
                 J_inter=0.25, 
                 trials=1000,
                 external_field_range=(-400, 400),
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
        self.num_factions = min(12, max(3, self.N // 5 + 2))
        self.faction_map = initialize_factions(self.N, self.num_factions, self.random)
        self.h_values = generate_h_values(self.num_factions, self.external_field_range, self.random)
        self.h_map = generate_h_map(self.faction_map, self.h_values)

        self.current_trial = 0
        self.energies = [get_total_energy(self.lattice, self.faction_map, self.h_map, self.J_intra, self.J_inter)]

        self.snapshots = []

    def _flip_probability(self, row, col):
        delta = (get_energy_faction(row, col, -1, self.lattice, self.faction_map, self.h_map, self.J_intra, self.J_inter) -
                 get_energy_faction(row, col,  1, self.lattice, self.faction_map, self.h_map, self.J_intra, self.J_inter))
        if delta <= 0:
            return 1.0
        else:
            return np.exp(-delta / self.T)

    def step(self, num_steps=1, record_snapshots=False):
        for _ in range(num_steps):
            row, col = self.random.integers(0, self.N, size=2)
            prob = self._flip_probability(row, col)
            if self.random.random() <= prob:
                delta = (get_energy_faction(row, col, -1, self.lattice, self.faction_map, self.h_map, self.J_intra, self.J_inter) -
                         get_energy_faction(row, col,  1, self.lattice, self.faction_map, self.h_map, self.J_intra, self.J_inter))
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
            'energies': np.array(self.energies) / (self.N * self.N),
            'current_trial': self.current_trial,
        }

    def get_spin_percentages(self):
        return get_spin_percentages(self.lattice, self.faction_map)

    def get_magnetization(self):
        return get_magnetization(self.lattice)

    def get_agreement_score(self):
        return get_agreement_score(self.lattice, self.N) 