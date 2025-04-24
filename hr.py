from reader import Reader


class HR:
    def __init__(self):
        self.sampling_rate = 250
        self.min_interval_bpm = 220
        self.calibration_data = []
        self.calibration_samples = 250
        self.reader = Reader(27)
        self.data = []
        self.data_max = 1250
        self.prev = 0
        self.curr = 0
        self.next = 0
        self.calibration = None

    def calibrate(self):
        mean_val = sum(self.calibration_data) / len(self.calibration_data)
        variance = sum((x - mean_val) ** 2 for x in self.calibration_data) / len(self.calibration_data)
        std_dev = variance ** 0.5

        # Set detection threshold and peak filter values based on the signal
        threshold = mean_val + 0.2 * std_dev  # Set a slightly above-average threshold to detect real peaks
        min_amplitude_diff = 0.25 * std_dev  # Require each peak to differ enough from its neighbors
        min_interval = int(60 / self.min_interval_bpm * self.sampling_rate)  # Minimum spacing between peaks in samples

        calibrations = {'threshold': threshold,
                        'mean_val': mean_val,
                        'variance': variance,
                        'std_dev': std_dev,
                        'min_amplitude_diff': min_amplitude_diff,
                        'min_interval': min_interval}
        return calibrations

    def get_beat_interval(self):
        beat_interval = 1
        if self.prev == 0 or self.curr == 0 or self.next == 0 or len(self.data) != 0:
            while self.prev == 0 or self.curr == 0 or self.next == 0:
                if self.reader.has_data():
                    self.data.append(self.reader.read_next())
            self.prev = self.data[0]
            self.curr = self.data[1]
            self.next = self.data[2]

        while True:
            self.next = self.reader.read_next()
            amplitude_diff = abs(self.curr - self.prev) + abs(self.curr - self.next)

            if (
                self.curr >= self.prev and
                self.curr <= self.next and
                amplitude_diff > self.calibration['threshold'] and
                beat_interval >= self.calibration['min_interval']
            ):
                self.data.clear()
                self.data.append(self.prev)
                self.data.append(self.curr)
                self.data.append(self.next)
                return beat_interval

            if len(self.calibration_data) > self.calibration_samples:
                self.calibration = self.calibrate()
                self.calibration_data.clear()

            self.calibration_data.append(self.next)
            self.prev = self.curr
            self.curr = self.reader.read_next()
            beat_interval += 1