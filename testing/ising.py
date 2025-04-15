import numpy as np
import plotext as pltxt

N = 20
trials = 500
lattice = np.random.randint(0, 2, size=(N, N)) * 2 - 1

energies = np.zeros((trials))

spin = [-1, 1]  # potential electron spins
J = 2           # Interaction Strength: J > 0 means spins like to align, J < 0  means they prefer to be opposite
h = 0.25        # External Field: h > 0 means bias towards spin up, h < 0 means bias towards spin down
T = 2.5         # Temperature: high T means volatile spins, low T means stable spins (Boltzman normalized)

def randomize():
    lattice = np.random.randint(0, 2, size=(N, N)) * 2 - 1

def output():
    for row in lattice:
        print(' '.join([
            '\033[94m-\033[0m' if x == -1 else '\033[91m+\033[0m'
            for x in row
        ]))
    print(f"+: {np.count_nonzero(lattice == 1)}, -: {np.count_nonzero(lattice == -1)}")
    

def get_energy(row, col, flip):
    spin = lattice[row, col] * flip
    right = col + 1 if col +1  < N else 0
    down = row + 1 if row + 1 < N else 0
    return -J * (spin * lattice[down, col] + spin * lattice[row, right]) - h * spin

def get_total_energy():
    total_energy = 0
    for row in range(N):
        for col in range(N):
            total_energy += get_energy(row, col, 1)
    return total_energy

def get_probability(delta):
    return np.exp(-1*delta / T)

def flip_probability(row, col):
    delta = get_energy(row, col, -1) - get_energy(row, col, 1) # ∆E ≤ 0, lower energy, flip the spin
    if delta <= 0:
        return 1
    else:
        return get_probability(delta)

output()

total_energy = get_total_energy()

print(f"energy: {total_energy}", '\n')

changes = 0

for i in range(trials):
    energies[i] = get_total_energy()

    row, col = np.random.randint(0, N, size=2)
    r = np.random.rand(1, 1)
    probability = flip_probability(row, col)
    if(r <= probability):
        changes += 1
        lattice[row, col] *= -1

output()

total_energy = get_total_energy()

print(f"energy: {total_energy}", f"changes: {changes}",  '\n')

pltxt.theme('pro')
pltxt.scatter(energies, marker='braille')

pltxt.show()