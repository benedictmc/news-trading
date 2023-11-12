import numpy as np
import matplotlib.pyplot as plt

def compute_decayed_delta(trades, alpha=0.5):
    # Calculate velocity (in this case, just the trade values since we're looking at buy/sell separately)
    velocity = np.array(trades) 
    
    # Compute the delta (difference in velocity)
    delta = np.diff(velocity, prepend=velocity[0])
    
    # Apply exponential decay to the deltas
    decayed_delta = np.zeros_like(delta)
    decayed_delta[0] = delta[0]
    for i in range(1, len(delta)):
        decayed_delta[i] = delta[i] + (1 - alpha) * decayed_delta[i-1]
    
    return decayed_delta

# Sample data
buy_trades = [65.0, 120.0, 262.0, 471.0, 816.0, 1538.0, 2055.0, 2243.0, 2648.0]
sell_trades = [110.0, 311.0, 649.0, 1221.0, 2077.0, 2850.0, 3358.0, 3460.0, 3595.0]

buy_decayed_delta = compute_decayed_delta(buy_trades)
sell_decayed_delta = compute_decayed_delta(sell_trades)

# Plotting
time_stamps = [f"2023-09-12 21:09:{i:02}" for i in range(4, 4 + len(buy_trades))]
plt.figure(figsize=(12, 6))
plt.plot(time_stamps, buy_decayed_delta, label='Buy Decayed Delta', marker='o')
plt.plot(time_stamps, sell_decayed_delta, label='Sell Decayed Delta', marker='x')
plt.xticks(rotation=45)
plt.legend()
plt.xlabel('Timestamp')
plt.ylabel('Decayed Delta')
plt.title('Decayed Delta for Buy and Sell Trades')
plt.grid(True)
plt.tight_layout()
plt.savefig("decay.png")