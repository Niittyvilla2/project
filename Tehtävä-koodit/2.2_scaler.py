from filefifo import Filefifo

data = Filefifo(10, name = 'capture_250Hz_03.txt')
high = data.get()
low = high

for _ in range(499):
    d = data.get()
    if d > high:
        high = d
    if d < low:
        low = d

for _ in range(2500):
    item = data.get()
    item -= low
    item /= ((high - low) / 100)
    item = round(item, 2)
    print(item)