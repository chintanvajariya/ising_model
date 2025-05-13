import numpy as np

def inject_event(lattice, event_strength, random):
    beta = 0.25  # strength scaling factor

    desired_spin = np.sign(event_strength)
    misaligned_mask = lattice != desired_spin

    prob_flip = np.abs(event_strength) * beta
    rand_vals = random.random(lattice.shape)
    flip_mask = (rand_vals < prob_flip) & misaligned_mask

    lattice[flip_mask] *= -1
    return np.sum(flip_mask)

def create_decay_schedule(initial_strength, decay_rate, num_steps):
    schedule = []
    current_strength = initial_strength
    
    for _ in range(num_steps):
        if abs(current_strength) > 0.01:
            schedule.append(("field", current_strength * decay_rate))
            current_strength *= (1 - decay_rate)
    
    return schedule 