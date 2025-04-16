import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from scipy.ndimage import convolve
from numba import njit

N = 20
trials = 1000
lattice = np.random.randint(0, 2, size=(N, N)) * 2 - 1

energies = np.zeros((trials))

spin = [-1, 1]  # potential magnetic spins
J = 2           # Interaction Strength: J > 0 means spins like to align, J < 0  means they prefer to be opposite
h = 0.25        # External Field: h > 0 means bias towards spin up, h < 0 means bias towards spin down
T = 2.5         # Temperature: high T means volatile spins, low T means stable spins (Boltzman normalized)

J_intra = 2.0   # Interaction Strength between particles in the faction
J_inter = 0.5   # Interaction Strength between particles of different factions

def num_factions(N):
    return min(12, max(3, N // 5 + 2))

num_factions = num_factions(N)

# h is external field, generating unique values for each faction
def generate_h_values(num_factions):
    rng = np.random.default_rng()
    h_vals = []
    while len(h_vals) < num_factions:
        val = round(rng.uniform(-1.5, 1.5), 2)
        if abs(val) >= 0.1:
            h_vals.append(val)
    return h_vals

h_values = generate_h_values(num_factions)

show_borders = True  # toggleable

laplace_kernel = np.array([[0.05, 0.2, 0.05],
                            [0.2, -1.0, 0.2],
                            [0.05, 0.2, 0.05]])

# generating reaction-diffusion patterns
def generate_pattern(steps=10000, Du=0.16, Dv=0.08, F=0.060, k=0.062):
    U = np.ones((N, N))
    V = np.zeros((N, N))

    rng = np.random.default_rng()
    for _ in range(20):

        margin = max(1, N // 10)
        i, j = rng.integers(margin, N - margin, size=2)

        U[i-2:i+2, j-2:j+2] = 0.50
        V[i-2:i+2, j-2:j+2] = 0.25

    for step in range(steps):
        Lu = convolve(U, laplace_kernel, mode='wrap')
        Lv = convolve(V, laplace_kernel, mode='wrap')

        UVV = U * V * V
        U += Du * Lu - UVV + F * (1 - U)
        V += Dv * Lv + UVV - (F + k) * V

        U = np.clip(U, 0, 1)
        V = np.clip(V, 0, 1)

    return V


# places factions across the grid
def assign_factions():
    rng = np.random.default_rng()

    faction_map = -1 * np.ones((N, N), dtype=int)
    visited = np.zeros((N, N), dtype=bool)
    frontier = []

    # seed one random center per faction
    centers = rng.choice(N * N, size=num_factions, replace=False)
    centers = np.column_stack(np.unravel_index(centers, (N, N)))

    for faction_id, (r, c) in enumerate(centers):
        faction_map[r, c] = faction_id
        visited[r, c] = True
        frontier.append((r, c, faction_id))

    # expand each blob until the full grid is covered
    while frontier:
        r, c, faction_id = frontier.pop(0)
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < N and 0 <= nc < N):
                continue  # skip out-of-bounds neighbors
            if not visited[nr, nc]:
                faction_map[nr, nc] = faction_id
                visited[nr, nc] = True
                frontier.append((nr, nc, faction_id))

    return faction_map

# correlate h values with each faction
def generate_h_map(faction_map):
    h_map = np.zeros_like(faction_map, dtype=float)
    unique_factions = np.unique(faction_map)
    for i, faction in enumerate(unique_factions):
        h_map[faction_map == faction] = h_values[i]
    return h_map

# compute energy now with faction effects
@njit
def get_energy_faction(row, col, flip, lattice, faction_map, h_map):
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
        if faction_map[row, col] == faction_map[r, c]:
            J = J_intra
        else:
            J = J_inter
        energy += -J * spin * lattice[r, c]
    energy += -h_map[row, col] * spin
    return energy


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
    return np.exp(-delta / T)

def flip_probability(row, col): # ∆E ≤ 0, lower energy, flip the spin
    delta = get_energy_faction(row, col, -1, lattice, faction_map, h_map) - get_energy_faction(row, col, 1, lattice, faction_map, h_map) 
    if delta <= 0:
        return 1
    else:
        return np.exp(-delta / T)


# initialize plot layout
def init_plot(faction_map):
    global show_borders
    N = lattice.shape[0]
    fig = plt.figure(figsize=(10, 6), facecolor='black')
    gs = fig.add_gridspec(2, 2, width_ratios=[3, 2], height_ratios=[1, 1], wspace=0.3, hspace=0.4)

    ax_lattice = fig.add_subplot(gs[:, 0])
    ax_energy = fig.add_subplot(gs[0, 1])
    ax_hist = fig.add_subplot(gs[1, 1])

    ax_lattice.set_xlim(0, N)
    ax_lattice.set_ylim(0, N)
    ax_lattice.invert_yaxis()
    ax_lattice.set_aspect('equal')
    ax_lattice.axis('off')
    ax_lattice.set_title("Spin Lattice with Factions", fontsize=16, color='white', pad=12)

    for ax in [ax_energy, ax_hist]:
        ax.set_facecolor('#1e1e1e')
        ax.tick_params(colors='white')
        for spine in ax.spines.values():
            spine.set_color('white')

    ax_energy.set_title("Energy Over Time", fontsize=12, color='white')
    ax_energy.set_xlabel("Trial", color='white')
    ax_energy.set_ylabel("Energy", color='white')

    ax_hist.set_title("Spin Distribution Per Faction", fontsize=12, color='white')
    ax_hist.set_xlabel("Faction ID", color='white')
    ax_hist.set_ylabel("Net Spin", color='white')

    return fig, ax_lattice, ax_energy, ax_hist


# update plot layout
def update_plot(ax_lattice, ax_energy, ax_hist, faction_map, trial_num):
    global show_borders

    for patch in ax_lattice.patches[:]:
        patch.remove()
    
    for collection in ax_lattice.collections[:]:
        collection.remove()

    for txt in ax_lattice.texts[1:]:
        txt.remove()

    ax_energy.cla()
    ax_hist.cla()

    spin_colors = {1: '#e63946', -1: '#457b9d'}
    N = lattice.shape[0]

    faction_ids = np.unique(faction_map)
    flat_factions = faction_map.ravel()
    flat_lattice = lattice.ravel()
    net_spins = np.bincount(flat_factions, weights=flat_lattice, minlength=np.max(faction_ids) + 1)

    max_pos = max([s for s in net_spins if s > 0], default=1)
    max_neg = min([s for s in net_spins if s < 0], default=-1)

    spin_percentages = []

    for f in faction_ids:
        mask = faction_map == f
        total = np.sum(mask)
        if total == 0:
            spin_percentages.append(0)
        else:
            net_spin = np.sum(lattice[mask])  # since spins are +1 and -1
            percent = round(100 * net_spin / total, 2)
            spin_percentages.append(percent)

    # draw red/blue cells based on spin 
    spin_colors = {1: np.array([230, 57, 70]) / 255, -1: np.array([69, 123, 157]) / 255}
    for row in range(N):
        for col in range(N):
            spin = lattice[row, col]
            color = spin_colors[spin]
            rect = patches.Rectangle((col, row), 1, 1, facecolor=color, edgecolor='none')
            ax_lattice.add_patch(rect)

    # overlay tint per faction
    max_abs_spin = np.max(np.abs(net_spins)) if net_spins.size > 0 else 1
    for i, faction in enumerate(faction_ids):
        ys, xs = np.where(faction_map == faction)
        if len(xs) > 0:
            alpha = 0.4  # max tint
            net = net_spins[i]
            if net > 0:
                strength = net / max_pos if max_pos else 0
                color = (0.6, 0.3, 0.4, alpha * strength)  # red overlay
            elif net < 0:
                strength = net / max_neg if max_neg else 0
                color = (0.3, 0.5, 0.6, alpha * strength)  # blue overlay
            else:
                continue
            for y, x in zip(ys, xs):
                tint = patches.Rectangle((x, y), 1, 1, facecolor=color, edgecolor='none')
                ax_lattice.add_patch(tint)


    # thin gridlines
    for row in range(N + 1):
        ax_lattice.plot([0, N], [row, row], color='white', linewidth=0.5, alpha=0.2)
    for col in range(N + 1):
        ax_lattice.plot([col, col], [0, N], color='white', linewidth=0.5, alpha=0.2)

    # draw dim + and -
    for row in range(N):
        for col in range(N):
            spin = lattice[row, col]
            symbol = "+" if spin == 1 else "−"
            color = "#ffb3b3" if spin == 1 else "#a3c4dc"
            ax_lattice.text(
                col + 0.5, row + 0.5, symbol,
                color=color,
                fontsize=6, ha='center', va='center',
                alpha=0.7
            )

    # borders between factions
    if show_borders:
        for row in range(N):
            for col in range(N):
                curr = faction_map[row, col]
                for dr, dc in [(0, 1), (1, 0)]:
                    nr, nc = row + dr, col + dc
                    if nr >= N or nc >= N:
                        continue
                    neighbor = faction_map[nr, nc]
                    if curr != neighbor:
                        x0, y0 = col, row
                        if dr == 1:
                            x1, y1 = x0 + 1, y0 + 1
                            line = [(x0, y1), (x1, y1)]
                        else:
                            x1, y1 = x0 + 1, y0 + 1
                            line = [(x1, y0), (x1, y1)]
                        ax_lattice.plot(*zip(*line), color='white', linewidth=2)

    # faction labels centered
    for f in faction_ids:
        ys, xs = np.where(faction_map == f)
        if len(xs) > 0:
            center_x, center_y = np.mean(xs), np.mean(ys)
            ax_lattice.text(center_x + 0.5, center_y + 0.5, str(f + 1),
                            color='white', fontsize=11, ha='center', va='center',
                            bbox=dict(facecolor='black', edgecolor='none', alpha=0.5, boxstyle='circle'))
            
    # spin-up/down counter
    spin_up = np.count_nonzero(lattice == 1)
    spin_down = np.count_nonzero(lattice == -1)
    summary_text = f"↑ {spin_up}   ↓ {spin_down}"

    ax_lattice.text(N // 2, N + 1.5, summary_text,
                    ha='center', va='bottom', fontsize=11,
                    color='white', bbox=dict(facecolor='black', edgecolor='none', alpha=0.6))


    # energy chart
    ax_energy.set_facecolor('#1e1e1e')
    ax_energy.plot(energies[:trial_num + 1], color='white')
    ax_energy.set_title("Energy Over Time", fontsize=12, color='white')
    ax_energy.set_xlabel("Trial", color='white')
    ax_energy.set_ylabel("Energy", color='white')
    ax_energy.tick_params(colors='white')
    for spine in ax_energy.spines.values():
        spine.set_color('white')

    # spin histogram
    net_spin_values = [net_spins[f] for f in faction_ids]

    bar_container = ax_hist.bar(faction_ids + 1, spin_percentages, color='#f4a261')
    tick_positions = [bar.get_x() + bar.get_width() / 2 for bar in bar_container]
    ax_hist.set_xticks(tick_positions)
    ax_hist.set_xticklabels([str(f + 1) for f in faction_ids])
    ax_hist.set_yticks([-100, -50, 0, 50, 100])
    ax_hist.set_yticklabels(['−100%', '−50%', '0%', '50%', '100%'])
    ax_hist.set_ylabel("% Net Spin", color='white')
    ax_hist.axhline(0, color='white', linewidth=1, linestyle='--', alpha=0.5)

    ax_hist.set_title("Spin Distribution Per Faction", fontsize=12, color='white')
    ax_hist.set_xlabel("Faction ID", color='white')
    ax_hist.set_facecolor('#1e1e1e')
    ax_hist.tick_params(colors='white')
    for spine in ax_hist.spines.values():
        spine.set_color('white')

    plt.pause(0.001)



V = generate_pattern(steps=3000)
faction_map = assign_factions()
h_map = generate_h_map(faction_map)
energies[0] = get_total_energy()

plt.ion()
fig, ax_lattice, ax_energy, ax_hist = init_plot(faction_map)

for i in range(trials):
    row, col = np.random.randint(0, N, size=2)
    delta = get_energy_faction(row, col, -1, lattice, faction_map, h_map) - get_energy_faction(row, col, 1, lattice, faction_map, h_map)

    r = np.random.rand(1, 1)
    probability = flip_probability(row, col)
    
    if r <= probability:
        lattice[row, col] *= -1
        energies[i + 1] = energies[i] + delta
    else:
        energies[i + 1] = energies[i]

    if i % 10 == 0:
        update_plot(ax_lattice, ax_energy, ax_hist, faction_map, i)

plt.ioff()
plt.show()