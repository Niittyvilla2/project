from filefifo import Filefifo

# Configuration
filename = 'capture01_250Hz.txt'      # Name of the dataset file to use
sampling_rate = 250                   # Sampling rate in Hz (250 samples per second)
calibration_samples = 250            # How many samples to use for calibration (1 second)
max_samples = 45000                   # Max number of total samples to read
max_peaks = 1000                       # Max number of peaks to detect
min_bpm = 40                          # Minimum valid BPM
max_bpm = 220                         # Maximum valid BPM
min_interval_bpm = 200               # For min_interval spacing: assume no beats faster than 200 BPM

# Calibration
data = Filefifo(10, name=filename)               # Open the file for initial sampling

def calibration(fifo):

    calibration_data = fifo  # Read 250 values for calibration

    # Calculate mean and standard deviation of the calibration data
    mean_val = sum(calibration_data) / len(calibration_data)
    variance = sum((x - mean_val) ** 2 for x in calibration_data) / len(calibration_data)
    std_dev = variance ** 0.5

    # Set detection threshold and peak filter values based on the signal
    threshold = mean_val + 0.2 * std_dev                       # Set a slightly above-average threshold to detect real peaks
    min_amplitude_diff = 0.25 * std_dev                        # Require each peak to differ enough from its neighbors
    min_interval = int(60 / min_interval_bpm * sampling_rate)  # Minimum spacing between peaks in samples
    
    calibrations = {'threshold':threshold,
                    'mean_val':mean_val,
                    'variance':variance,
                    'std_dev':std_dev,
                    'min_amplitude_diff':min_amplitude_diff,
                    'min_interval':min_interval}
    return calibrations

# Debug: Printing calculated values
#print("Calibrated threshold:", threshold)
#print("Minimum amplitude diff:", min_amplitude_diff)
#print("Minimum interval between peaks (samples):", min_interval)

# Peak detection
#data = Filefifo(10, name=filename)   # Re-open file from the start for actual peak detection

last = data.get()                    # Get the first value
current = data.get()                 # Get the second value
sample_index = 2                     # Start tracking sample index from 2
peaks = []                           # Store sample indices of detected peaks
samples_read = 2                     # Count how many samples we’ve read so far
cal_data = [data.get() for _ in range(calibration_samples)]
cal = calibration(cal_data)
cal_data.clear()
last_peak_index = -75      # Prevent first peak from being falsely accepted

# Read data and detect peaks
while samples_read < max_samples and len(peaks) < max_peaks:
    next_val = data.get()            # Read the next sample from the stream
    samples_read += 1               # Count the sample

    # Calculate how much current value differs from neighbors
    amplitude_diff = abs(current - last) + abs(current - next_val)

    # Check for peak conditions:
    if (
        current >= last and                                          # Local maximum condition (greater than previous)
        current <= next_val and                                      # Local maximum condition (greater than next)
        current > cal['threshold'] and                               # Above dynamic threshold
        amplitude_diff > cal['min_amplitude_diff'] and               # Stands out enough from neighbors
        (sample_index - 1 - last_peak_index) >= cal['min_interval']  # Spaced out enough from last peak
    ):
        peaks.append(sample_index - 1)           # Record the sample index of the peak
        print(sample_index)
        last_peak_index = sample_index - 1       # Update last peak index
        
    if len(cal_data) > 250:
        cal = calibration(cal_data)
        print(cal)
        cal_data.clear()
    cal_data.append(next_val)

    # Move the 3-sample window forward
    last = current
    current = next_val
    sample_index += 1
    
# Debuggin: How many peaks were detected
#print("Total peaks detected:", len(peaks))

# Debugging: Printing raw sample intervals between peaks
#print("\nRaw peak intervals (in samples):")
#for i in range(1, len(peaks)):
    #print(f"{i}: {peaks[i] - peaks[i - 1]} samples")

# Calculating BPM Values from intervals
print(len(peaks))
print("\nBPM from each interval:")
bpm_sum = 0
bpm_count = 0

# Loop through all intervals between peaks
for i in range(1, len(peaks)):
    interval = peaks[i] - peaks[i - 1]               # Get sample difference between two peaks

    if interval > 0:
        bpm = 60 * sampling_rate / interval          # Convert interval (samples) into BPM

        # Filter out suspiciously short spikes (isolated fast beats)
        if interval < 200 and (i == 1 or interval < 0.75 * (peaks[i - 1] - peaks[i - 2])):
            print(f"Filtered spike: {bpm:.2f} BPM (suspiciously short)")
        elif min_bpm <= bpm <= max_bpm:
            bpm_sum += bpm
            bpm_count += 1
            print(f"Interval {bpm_count}: {bpm:.2f} BPM")
        else:
            print(f"Filtered out: {bpm:.2f} BPM (outside {min_bpm}-{max_bpm})")

# Output Average BPM
if bpm_count > 0:
    avg_bpm = bpm_sum / bpm_count
    print("\nAverage BPM: {:.2f}".format(avg_bpm))
else:
    print("\nNo valid BPM intervals detected.")

