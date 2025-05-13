from numba import njit

@njit
def get_energy_faction(row, col, flip, lattice, faction_map, h_map, J_intra, J_inter):
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

def get_total_energy(lattice, faction_map, h_map, J_intra, J_inter):
    total = 0
    N = lattice.shape[0]
    for row in range(N):
        for col in range(N):
            total += get_energy_faction(row, col, 1, lattice, faction_map, h_map, J_intra, J_inter)
    return total 