# Factional Ising Model Simulation

[**Live Simulation**](https://ising-model-6e5d.onrender.com)

This interactive website explores how complex group dynamics emerge across physics, politics, and finance, all through the lens of the Ising Model, reimagined with a factional twist.

---

## What Is the Ising Model?

The **Ising Model** is a classic simulation from statistical mechanics that shows how individual decisions can lead to large-scale behavior. Imagine a grid of people, each choosing between two options, like yes or no, buy or sell, or align or oppose. Each person is influenced by their neighbors and tends to conform to nearby choices. Over time, these local nudges can produce dramatic effects, like sudden consensus or deep polarization.

Originally used to model magnets, the Ising Model is now applied to fields ranging from biology to sociology, anywhere collective patterns emerge from simple rules.

---

## A New Interpretation: Factionalism

While the Ising Model has long been used to explain phase transitions and collective alignment, this project introduces a **factional extension**, where agents are grouped into distinct "factions" with their own internal preferences and varying levels of openness to outside influence.

This reinterpretation makes the model vastly more realistic for social and economic systems. It allows us to simulate how loyalty, cross-group tension, and randomness interact, leading to more grounded predictions and fewer idealized assumptions.

---

## Component 1: Ferromagnetism

This classic use case models atoms in a metal that want to align their spins with neighbors. As the **temperature** decreases, the system stabilizes into a uniform magnetic state. With the added faction logic, we visualize **domain boundaries** and **local alignment entropy**, showing how microscopic changes ripple into large-scale shifts.

<p align="center">
  <img src="https://github.com/user-attachments/assets/ab84a9d9-5a12-4363-8660-6ef097018950" width="750" alt="Ferromagnet Simulation">
</p>

---

## Component 2: Elections

What happens when voters are grouped by ideology or demographic? In this domain, factions represent political affiliations, and external fields simulate events like media campaigns. You can tune **intra-group loyalty**, **cross-group influence**, and **randomness** to watch polarized echo chambers emerge, or collapse into compromise.

<p align="center">
  <img src="https://github.com/user-attachments/assets/61c95bba-4eca-49dc-be9f-c8f78b70f9fa" width="750" alt="Election Simulation">
</p>

---

## Component 3: Stock Markets

Markets are full of traders acting on local signals and herd behavior. Here, factions represent trading styles, value investors, speculators, institutional players, each responding differently to volatility. The simulation lets you adjust each group's initial biases, showing how small adjustments can destabilize an entire ecosystem.

<p align="center">
  <img src="https://github.com/user-attachments/assets/8cb416cf-f89c-41f0-950a-8797fe464c89" width="750" alt="Stock Market Simulation">
</p>

---

## How the Model Works (if you're interested)

At the heart of the Ising Model is a simple idea: each agent (or “spin”) takes on a value of either +1 or –1 and tends to align with its neighbors. The system’s total energy is given by the formula:

E(σ) = -J ∑⟨i,j⟩ σᵢσⱼ - ∑ᵢ hᵢσᵢ

Where:
- σᵢ is the state of spin i (either +1 or –1),
- J controls how strongly spins want to align (higher J = stronger conformity),
- ⟨i,j⟩ denotes pairs of neighboring agents,
- hᵢ is the external influence (or bias) acting on agent i.

The goal of the system is to minimize its energy, which happens by choosing one at random agent and temporarily flipping their value, from +1 to -1 or vice-versa. If doing so decreases the system's energy, we make the flip permanent. This energy decreases if the agent's charge is similar to enough of its neighbors. Otherwise, we move on and repeat the process, so as local alignment betewen agents increases, the value of E across the system decreases. There are a few more quirks related to different probabilities, but you can read [this article](https://stanford.edu/~jeffjar/statmech/intro4.html) to better grasp the model intuitively.

---

## What This Project Shows

- A model built on just a few local rules can generate complex, global behavior
- Social, political, and economic systems can all be interpreted through shared mathematical structures
- Factional dynamics, long ignored in basic models, are essential for simulating real-world outcomes
- Interactive visualization can turn abstract equations into intuitive understanding

---

## What I Learned

- How to transform a physics model into a multi-domain, interactive experience
- Techniques for adding realism via factional logic, feedback loops, and parameter controls
- The power of modular simulation frameworks across disciplines
- A deeper appreciation for how collective behavior emerges from alignment, tension, and randomness

---

**The Ising Model isn’t just about magnets.** With the right structure, it becomes a window into how people organize, polarize, and react to change, across every domain that matters.

