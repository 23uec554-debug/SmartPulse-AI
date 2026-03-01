  import numpy as np
import matplotlib.pyplot as plt
import random
import os

# =============================
# Create results folder if missing
# =============================
os.makedirs("results", exist_ok=True)

# =============================
# Simulation Parameters
# =============================

SIM_TIME = 10000
E_TX = 1.0
BATTERY_CAPACITY = 10000
LAMBDA_ENERGY = 1.0

PERIODIC_RATES = [0.01, 0.02, 0.05, 0.1, 0.2]
THRESHOLDS = [5, 10, 20, 50, 100]

np.random.seed(42)
random.seed(42)

# =============================
# Realistic Sensor Signal
# =============================

def generate_sensor_signal(t):
    """
    Simulates a slowly varying environmental signal
    (e.g., temperature) with noise.
    """
    base = 25 + 2 * np.sin(0.01 * t)
    noise = np.random.normal(0, 0.2)
    return base + noise

# =============================
# Fixed-Rate Sensing
# =============================

def simulate_periodic(rate):
    AoI = 0
    total_aoi = 0
    energy = 0

    last_sent = generate_sensor_signal(0)
    received_series = []
    true_series = []

    for t in range(SIM_TIME):
        true_val = generate_sensor_signal(t)
        true_series.append(true_val)

        AoI += 1

        if random.random() < rate:
            AoI = 0
            energy += E_TX
            last_sent = true_val

        received_series.append(last_sent)
        total_aoi += AoI

    mse = np.mean((np.array(true_series) - np.array(received_series)) ** 2)
    lifetime = BATTERY_CAPACITY / (energy / SIM_TIME + 1e-6)

    return total_aoi / SIM_TIME, energy / SIM_TIME, mse, lifetime

# =============================
# AoI Threshold Sensing
# =============================

def simulate_threshold(thresh):
    AoI = 0
    total_aoi = 0
    energy = 0

    last_sent = generate_sensor_signal(0)
    received_series = []
    true_series = []

    for t in range(SIM_TIME):
        true_val = generate_sensor_signal(t)
        true_series.append(true_val)

        AoI += 1

        if AoI >= thresh:
            AoI = 0
            energy += E_TX
            last_sent = true_val

        received_series.append(last_sent)
        total_aoi += AoI

    mse = np.mean((np.array(true_series) - np.array(received_series)) ** 2)
    lifetime = BATTERY_CAPACITY / (energy / SIM_TIME + 1e-6)

    return total_aoi / SIM_TIME, energy / SIM_TIME, mse, lifetime

# =============================
# Reinforcement Learning Agent
# =============================

class QAgent:
    def __init__(self, max_aoi=200, lr=0.1, gamma=0.99, eps=0.1):
        self.max_aoi = max_aoi
        self.lr = lr
        self.gamma = gamma
        self.eps = eps
        self.Q = np.zeros((max_aoi + 1, 2))  # actions: 0=no_tx, 1=tx

    def act(self, state):
        if random.random() < self.eps:
            return random.choice([0, 1])
        return np.argmax(self.Q[state])

    def update(self, s, a, r, s_next):
        best_next = np.max(self.Q[s_next])
        self.Q[s, a] += self.lr * (
            r + self.gamma * best_next - self.Q[s, a]
        )

# =============================
# Adaptive Edge Intelligence
# =============================

def simulate_rl():
    agent = QAgent()
    AoI = 0
    last_sent = generate_sensor_signal(0)

    # -------- Training --------
    for t in range(50000):
        current_val = generate_sensor_signal(t)
        state = min(AoI, agent.max_aoi)
        action = agent.act(state)

        reward = -AoI
        if action == 1:
            reward -= LAMBDA_ENERGY
            AoI = 0
            last_sent = current_val
        else:
            AoI += 1

        next_state = min(AoI, agent.max_aoi)
        agent.update(state, action, reward, next_state)

    # -------- Evaluation --------
    AoI = 0
    total_aoi = 0
    energy = 0

    received_series = []
    true_series = []

    for t in range(SIM_TIME):
        true_val = generate_sensor_signal(t)
        true_series.append(true_val)

        action = np.argmax(agent.Q[min(AoI, agent.max_aoi)])

        if action == 1:
            energy += E_TX
            AoI = 0
            last_sent = true_val
        else:
            AoI += 1

        received_series.append(last_sent)
        total_aoi += AoI

    mse = np.mean((np.array(true_series) - np.array(received_series)) ** 2)
    lifetime = BATTERY_CAPACITY / (energy / SIM_TIME + 1e-6)

    return total_aoi / SIM_TIME, energy / SIM_TIME, mse, lifetime

# =============================
# Run Simulations
# =============================

periodic_results = [simulate_periodic(r) for r in PERIODIC_RATES]
periodic_aoi, periodic_en, periodic_mse, periodic_life = zip(*periodic_results)

threshold_results = [simulate_threshold(th) for th in THRESHOLDS]
threshold_aoi, threshold_en, threshold_mse, threshold_life = zip(*threshold_results)

rl_aoi, rl_en, rl_mse, rl_life = simulate_rl()

# =============================
# Plot 1: AoI Comparison
# =============================

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.plot(PERIODIC_RATES, periodic_aoi, "-o")
plt.xlabel("Transmission Rate")
plt.ylabel("Avg AoI")
plt.title("AoI vs Fixed-rate")
plt.grid()

plt.subplot(1, 2, 2)
plt.plot(THRESHOLDS, threshold_aoi, "-s")
plt.xlabel("Threshold (AoI)")
plt.ylabel("Avg AoI")
plt.title("AoI vs Threshold")
plt.grid()

plt.tight_layout()
plt.savefig("results/aoi_comparison.png", dpi=300)
plt.show()

# =============================
# Plot 2: Energy vs Monitoring Error
# =============================

plt.figure(figsize=(6, 5))
plt.scatter(periodic_en, periodic_mse, label="Fixed-rate sensing")
plt.scatter(threshold_en, threshold_mse, label="AoI-threshold sensing")
plt.scatter([rl_en], [rl_mse], label="Adaptive edge intelligence")
plt.xlabel("Avg Energy Usage")
plt.ylabel("Monitoring MSE")
plt.title("Energy vs Monitoring Fidelity")
plt.legend()
plt.grid()
plt.savefig("results/energy_vs_fidelity.png", dpi=300)
plt.show()

# =============================
# Plot 3: Battery Lifetime
# =============================

plt.figure(figsize=(6, 5))
plt.bar(
    ["Fixed", "Threshold", "Adaptive"],
    [np.mean(periodic_life), np.mean(threshold_life), rl_life],
)
plt.ylabel("Estimated Battery Lifetime")
plt.title("Battery Lifetime Comparison")
plt.grid(axis="y")
plt.savefig("results/battery_lifetime.png", dpi=300)
plt.show()

# =============================
# Final Results
# =============================

print("\n=== Adaptive Edge Intelligence Results ===")
print("Average AoI:", rl_aoi)
print("Average Energy:", rl_en)
print("Monitoring MSE:", rl_mse)
print("Estimated Battery Lifetime:", rl_life)
