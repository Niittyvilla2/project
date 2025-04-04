from filefifo import Filefifo

# choosing the .txt file with the data
data = Filefifo(10, name='data.3.txt')

sampling_rate = 250  # in Hz
last_value = data.get()
current_value = data.get()
sample_index = 2
peaks = [] #storing indexes (positions) for positive peaks

#collecting at least 4 peaks to get min. 3 intervals. works with more too
while len(peaks) < 4:
    next_value = data.get()
    if current_value >= last_value and current_value >= next_value: #checks if current value is greater than both its neighbors, if so, it's peak
        peaks.append(sample_index - 1)  # index of the peak
    last_value = current_value
    current_value = next_value
    sample_index += 1 #shifting values forward

# calculating peak intervals
print("Peak-to-peak intervals:")
for i in range(1, len(peaks)):
    samples = peaks[i] - peaks[i - 1] #calculates the number of samples between each peak
    seconds = samples / sampling_rate #converts into seconds
    print(f"Interval {i}: {samples} samples = {seconds:.3f} seconds")

#calculating frequency from average interval
intervals = [peaks[i] - peaks[i - 1] for i in range(1, len(peaks))] #list of sample distances between peaks
avg_interval_samples = sum(intervals) / len(intervals) #average time (in samples) between peaks
frequency = sampling_rate / avg_interval_samples #how many peaks happen in 1 second
print(f"Estimated frequency: {frequency:.2f} Hz")
