from filefifo import Filefifo

data = Filefifo(10, name='capture03_250Hz.txt')  # Use 1, 2, or 3

sampling_rate = 250  # Hz
window_size = sampling_rate * 2  # 2 seconds = 500 samples

# Load initial window for threshold
sample_window = [data.get() for _ in range(window_size)]
avg = sum(sample_window) / len(sample_window)
max_val = max(sample_window)
min_val = min(sample_window)

# Smart threshold: above average, closer to max
threshold = avg + 0.35 * (max_val - avg)

# Reset detection
last_value = sample_window[-2]
current_value = sample_window[-1]
sample_index = window_size + 1
peaks = []

# Interval limits (samples)
min_interval_samples = int(sampling_rate * 0.33)  # ~180 BPM
max_interval_samples = int(sampling_rate * 2.0)   # ~30 BPM

# Peak detection loop
while len(peaks) < 30:  # get more than 21 so we can filter
    next_value = data.get()

    if (current_value > threshold and
        current_value >= last_value and
        current_value >= next_value and
        (len(peaks) == 0 or (sample_index - 1 - peaks[-1]) >= min_interval_samples)):
        peaks.append(sample_index - 1)

    last_value = current_value
    current_value = next_value
    sample_index += 1

# Calculate heart rate values
print("Heart Rates (BPM) based on peak-to-peak intervals:")
valid_hrs = []

for i in range(1, len(peaks)):
    interval_samples = peaks[i] - peaks[i - 1]
    interval_seconds = interval_samples / sampling_rate
    hr = 60 / interval_seconds

    # Filtering out abnormal heart rates
    if 45 <= hr <= 190:
        valid_hrs.append(hr)
        print(f"Interval {i}: {interval_samples} samples -> {interval_seconds:.3f} sec -> HR: {hr:.2f} BPM")
    else:
        print(f"Interval {i}: {interval_samples} samples -> HR: {hr:.2f} BPM (rejected)")

if valid_hrs:
    avg_hr = sum(valid_hrs) / len(valid_hrs)
    print(f"Average heart rate from valid intervals: {avg_hr:.2f} BPM")
else:
    print("No valid heart rate readings found.")
