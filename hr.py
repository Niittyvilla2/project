from reader import Reader


class HR:
    def __init__(self, ppg):
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
        self.show_ppg = False
        self.ppg = ppg
        self.ppg_points = []
        self.squish = 3

    def calibrate(self):
        mean_val = sum(self.calibration_data) / len(self.calibration_data)
        variance = sum((x - mean_val) ** 2 for x in self.calibration_data) / len(self.calibration_data)
        std_dev = variance ** 0.5

        # Set detection threshold and peak filter values based on the signal
        threshold = mean_val + 0.3 * std_dev  # Set a slightly above-average threshold to detect real peaks
        min_amplitude_diff = 0.33 * std_dev  # Require each peak to differ enough from its neighbors
        min_interval = int(
            60 / self.min_interval_bpm * 1000 / self.reader.interval)  # Minimum spacing between peaks in samples

        calibrations = {'threshold': threshold,
                        'mean_val': mean_val,
                        'variance': variance,
                        'std_dev': std_dev,
                        'min_amplitude_diff': min_amplitude_diff,
                        'min_interval': min_interval}
        return calibrations

    def get_beat_interval(self):
        beat_interval = 1
        show_counter = 0
        if self.prev == 0 and self.curr == 0 and self.next == 0:
            while len(self.data) < 3:
                i = 0
                for _ in range(self.squish):
                    data = self.reader.read_next()
                    i += data
                data = i / self.squish
                self.data.append(data)
                self.ppg_points.append(data)
            self.prev = self.data[0]
            self.curr = self.data[1]
            self.next = self.data[2]

        while True:
            if self.reader.has_data():
                self.next = self.reader.read_next()
                self.ppg_points.append(self.next)
                amplitude_diff = abs(self.curr - self.prev) + abs(self.curr - self.next)

                if self.calibration != None:
                    if (
                            self.curr >= self.prev and
                            self.curr <= self.next and
                            amplitude_diff > self.calibration['min_amplitude_diff'] and
                            self.curr > self.calibration['threshold'] and
                            beat_interval >= self.calibration['min_interval']
                    ):
                        self.data.clear()
                        self.data.append(self.prev)
                        self.data.append(self.curr)
                        self.data.append(self.next)
                        return beat_interval * self.reader.interval

                if len(self.ppg_points) > 128 * self.squish + 1:
                    self.ppg_points.pop(0)

                if show_counter > 8 * self.squish:
                    show_counter = 0
                    if self.show_ppg and len(self.ppg_points) > 128 * self.squish:
                        self.ppg.plot(self.ppg_points, self.squish)
                        self.ppg.screen.show()

                if len(self.calibration_data) > self.calibration_samples:
                    self.calibration = self.calibrate()
                    self.calibration_data.clear()

                self.calibration_data.append(self.next)
                self.prev = self.curr
                self.curr = self.next
                beat_interval += 1
                show_counter += 1

    def set_squish(self, squish):
        self.squish = squish

    def set_show_ppg(self, value):
        self.show_ppg = value
