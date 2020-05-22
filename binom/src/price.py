import matplotlib.pyplot as plt
import numpy as np


def binomial(n, S, K, r, v, t, PutCall):
    At = t / n
    u = np.exp(v * np.sqrt(At))
    d = 1. / u
    p = (np.exp(r * At) - d) / (u - d)

    stockvalue = np.zeros((n + 1, n + 1))
    stockvalue[0, 0] = S
    for i in range(1, n + 1):
        stockvalue[i, 0] = stockvalue[i - 1, 0] * u
        for j in range(1, i + 1):
            stockvalue[i, j] = stockvalue[i - 1, j - 1] * d

    optionvalue = np.zeros((n + 1, n + 1))
    for j in range(n + 1):
        if PutCall == "C":
            optionvalue[n, j] = max(0, stockvalue[n, j] - K)
        elif PutCall == "P":
            optionvalue[n, j] = max(0, K - stockvalue[n, j])

    for i in range(n - 1, -1, -1):
        for j in range(i + 1):
            if PutCall == "P":
                optionvalue[i, j] = max(0, K - stockvalue[i, j], np.exp(-r * At) * (
                    p * optionvalue[i + 1, j] + (1 - p) * optionvalue[i + 1, j + 1]))
            elif PutCall == "C":
                optionvalue[i, j] = max(0, stockvalue[i, j] - K, np.exp(-r * At) * (
                    p * optionvalue[i + 1, j] + (1 - p) * optionvalue[i + 1, j + 1]))
    return optionvalue[0, 0]


n = 10
S = 100
r = 0.06
K = 105
v = 0.4
t = 1.

y = [-binomial(n, S, K, r, v, t, "C")] * (K)
y += [x - binomial(n, S, K, r, v, t, "C") for x in range(K)]

plt.plot(range(2 * K), y)
plt.axis([0, 2 * K, min(y) - 10, max(y) + 10])
plt.xlabel('Underlying asset price')
plt.ylabel('Profits')
plt.axvline(x=K, linestyle='--', color='black')
plt.axhline(y=0, linestyle=':', color='black')
plt.title('American Call Option')
plt.text(105, 0, 'K')
plt.show()

print("American Call Price: %s" % (binomial(n, S, K, r, v, t, PutCall="C")))

z = [-x + K - binomial(n, S, K, r, v, t, "P") for x in range(K)]
z += [-binomial(n, S, K, r, v, t, "P")] * (K)

plt.plot(range(2 * K), z, color='red')
plt.axis([0, 2 * K, min(y) - 10, max(y) + 10])
plt.xlabel('Underlying asset price')
plt.ylabel('Profits')
plt.axvline(x=K, linestyle='--', color='black')
plt.axhline(y=0, linestyle=':', color='black')
plt.title('American Put Option')
plt.text(105, 0, 'K')
plt.show()

print("American Put Price: %s" % (binomial(n, S, K, r, v, t, PutCall="P")))
