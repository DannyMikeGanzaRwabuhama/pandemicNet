import numpy as np

np.random.seed(42)
n_samples = 1000

direct_contacts = np.random.poisson(lam=2, size=n_samples).clip(0, 10)
days_since_last = np.random.exponential(scale=5, size=n_samples).clip(0, 30).astype(int)
mutual_contacts = np.random.binomial(n=5, p=0.3, size=n_samples).clip(0, 5)

X = np.column_stack((direct_contacts, days_since_last, mutual_contacts))

probs = (
    0.6 * (direct_contacts / 10) +
    0.3 * (1 - days_since_last / 30) +
    0.1 * (mutual_contacts / 5)
).clip(0.05, 0.95)
noise = np.random.uniform(-0.1, 0.1, n_samples)
probs = (probs + noise).clip(0.05, 0.95)
y = (probs > 0.4).astype(int)

# Debug
print("Sample X[:5]:\n", X[:5])
print("Sample probs[:5]:", probs[:5])
print("Sample y[:5]:", y[:5])
print(f"Met ratio: {y.mean():.2f}")
print(f"Correlation X vs. y:\n{np.corrcoef(X.T, y)[:-1, -1]}")

np.savez('contact_data.npz', X=X, y=y)