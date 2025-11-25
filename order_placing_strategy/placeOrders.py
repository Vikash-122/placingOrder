import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import random
import config

# -----------------------------
# Simulation Parameters
# -----------------------------
np.random.seed(42)
num_intervals = 50  # number of time intervals
venues = config.VENUES
total_order = config.TOTAL_ORDER  # total shares to buy
iceberg_visible = config.ICEBERG_VISIBLE  # visible portion per iceberg order
skip_threshold = config.SKIP_THRESHOLD  # skip if price moves >0.5% against us
# -----------------------------
data = {}
for venue in venues:
    prices = np.cumsum(np.random.normal(0, 0.2, num_intervals)) + 100  # start around 100
    volumes = np.random.randint(5000, 20000, num_intervals)
    data[venue] = pd.DataFrame({'Price': prices, 'Volume': volumes})

# Calculate VWAP for each venue
for venue in venues:
    df = data[venue]
    vwap = (df['Price'] * df['Volume']).sum() / df['Volume'].sum()
    data[venue]['VWAP'] = vwap

# -----------------------------
# Dynamic Allocation: TWAP timing + VWAP sizing
# -----------------------------
remaining_order = total_order
interval_sizes = []

# Compute total volume across all venues per interval
total_volumes = [sum(data[v].iloc[i]['Volume'] for v in venues) for i in range(num_intervals)]
volume_sum = sum(total_volumes)

for i in range(num_intervals):
    if remaining_order <= 0:
        interval_sizes.append(0)
    else:
        # Allocate proportionally to liquidity (VWAP principle)
        liquidity_ratio = total_volumes[i] / volume_sum
        size = min(int(total_order * liquidity_ratio), remaining_order)
        interval_sizes.append(size)
        remaining_order -= size

# -----------------------------
# Execution Simulation
# -----------------------------
executed_orders = []
executed_prices = []
venue_allocations = {v: 0 for v in venues}
liquidity_executed = []

for i in range(num_intervals):
    size = interval_sizes[i]
    if size == 0:
        liquidity_executed.append(0)
        continue

    # Skip trade if price moved up > threshold
    avg_price = np.mean([data[v].iloc[i]['Price'] for v in venues])
    if i > 0 and avg_price > np.mean([data[v].iloc[i-1]['Price'] for v in venues]) * (1 + skip_threshold):
        liquidity_executed.append(0)
        continue

    # Smart Order Routing: allocate based on best price and liquidity
    venue_scores = {}
    for v in venues:
        price = data[v].iloc[i]['Price']
        liquidity = data[v].iloc[i]['Volume']
        venue_scores[v] = liquidity / price  # simple score

    sorted_venues = sorted(venue_scores.items(), key=lambda x: x[1], reverse=True)

    remaining_chunk = size
    executed_this_interval = 0
    for v, _ in sorted_venues:
        if remaining_chunk <= 0:
            break
        alloc = min(remaining_chunk, random.randint(1000, 5000))
        venue_allocations[v] += alloc
        executed_orders.append(alloc)
        executed_prices.append(data[v].iloc[i]['Price'])
        remaining_chunk -= alloc
        executed_this_interval += alloc

    liquidity_executed.append(executed_this_interval)

# -----------------------------
# Performance Metrics
# -----------------------------
avg_exec_price = np.average(executed_prices, weights=executed_orders)
benchmark_vwap = np.mean([data[v]['VWAP'].iloc[0] for v in venues])
benchmark_twap = np.mean([np.mean(data[v]['Price']) for v in venues])

print("Execution Summary:")
print(f"Total Executed Shares: {sum(executed_orders)}")
print(f"Average Execution Price: {avg_exec_price:.2f}")
print(f"Benchmark VWAP: {benchmark_vwap:.2f}")
print(f"Benchmark TWAP: {benchmark_twap:.2f}")

# -----------------------------
# Visualizations with Matplotlib
# -----------------------------
schedule_df = pd.DataFrame({
    'Interval': range(num_intervals),
    'OrderSize': interval_sizes,
    'ExecutedSize': liquidity_executed,
    'AvgMarketPrice': [np.mean([data[v].iloc[i]['Price'] for v in venues]) for i in range(num_intervals)],
    'TotalLiquidity': total_volumes
})

# Plot Market Price and Executed Size
fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(schedule_df['Interval'], schedule_df['AvgMarketPrice'], color='blue', label='Avg Market Price')
ax1.set_xlabel('Interval')
ax1.set_ylabel('Market Price', color='blue')
ax2 = ax1.twinx()
ax2.bar(schedule_df['Interval'], schedule_df['ExecutedSize'], color='orange', alpha=0.5, label='Executed Size')
ax2.set_ylabel('Executed Size', color='orange')
plt.title('Market Price vs Executed Size')
fig.tight_layout()
plt.show()

# Plot Venue Allocation
plt.figure(figsize=(8, 5))
plt.bar(venue_allocations.keys(), venue_allocations.values(), color=['green', 'purple', 'gray'])
plt.title('Allocation Across Venues')
plt.xlabel('Venue')
plt.ylabel('Shares Executed')
plt.show()

# Plot Liquidity vs Executed Size
plt.figure(figsize=(10, 6))
plt.plot(schedule_df['Interval'], schedule_df['TotalLiquidity'], color='green', label='Total Liquidity')
plt.plot(schedule_df['Interval'], schedule_df['ExecutedSize'], color='red', label='Executed Size')
plt.title('Liquidity vs Executed Size')
plt.xlabel('Interval')
plt.ylabel('Shares')
plt.legend()
plt.show()

# -----------------------------
