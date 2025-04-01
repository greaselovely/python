import ping3
import time
import statistics
import matplotlib.pyplot as plt
import schedule
from datetime import datetime
import os

# Global variables to store metrics
latencies = []
ttls = []
jitters = []

def ping_host(host):
    global latencies, ttls, jitters
    
    try:
        latency = ping3.ping(host, unit='ms')
        if latency is not None:
            ttl = ping3.ping(host, ttl=True)
            latencies.append(latency)
            
            # Handle the case where TTL might be False
            if ttl is not False:
                ttls.append(ttl)
            else:
                ttls.append(None)  # or you could use a sentinel value like -1
            
            if len(latencies) > 1:
                jitter = abs(latencies[-1] - latencies[-2])
                jitters.append(jitter)
            
            print(f"Latency: {latency:.2f}ms, TTL: {ttl if ttl is not False else 'N/A'}")
        else:
            print("Host unreachable")
    except Exception as e:
        print(f"Error: {e}")

def plot_metrics():
    timestamps = [i for i in range(len(latencies))]
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 15))
    
    ax1.plot(timestamps, latencies)
    ax1.set_title('Latency over time')
    ax1.set_ylabel('Latency (ms)')
    
    # Filter out None values for TTL plot
    valid_ttls = [(t, ttl) for t, ttl in zip(timestamps, ttls) if ttl is not None]
    if valid_ttls:
        t, y = zip(*valid_ttls)
        ax2.plot(t, y)
    ax2.set_title('TTL over time')
    ax2.set_ylabel('TTL')
    
    ax3.plot(timestamps[1:], jitters)
    ax3.set_title('Jitter over time')
    ax3.set_ylabel('Jitter (ms)')
    
    for ax in (ax1, ax2, ax3):
        ax.set_xlabel('Minutes')
        ax.grid(True)
    
    plt.tight_layout()
    
    # Create 'plots' directory if it doesn't exist
    os.makedirs('plots', exist_ok=True)
    
    # Save the plot with current date and time as filename
    filename = f"plots/network_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename)
    print(f"Plot saved as {filename}")
    
    # Clear the figure to free up memory
    plt.close(fig)

def main():
    host = input("Enter the host to ping: ")
    
    # Schedule pinging every minute
    schedule.every(1).minutes.do(ping_host, host)
    
    # Schedule plotting every 8 hours
    schedule.every(8).hours.do(plot_metrics)
    
    print(f"Starting to ping {host} every minute. Plots will be generated every 8 hours.")
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()