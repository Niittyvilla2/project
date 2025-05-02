from reader import Reader
from hr import HR
from machine import RTC
import math

class Analysis:
    def __init__(self):
        self.reader = Reader(27)
        self.hr = HR()  
        self.rtc = RTC()
    def calculate(self):
        ppi = [5,3,5,6] #list of ppi's
        hr = [5,3,5,6] #list of hr's
        mean_hr = sum(hr)/len(hr)
        mean_ppi = sum(ppi)/len(ppi)
        i = 0
        ppisum = []
        
        for _ in range (len(ppi)):
            a = (ppi[i]-mean_ppi)**2
            ppisum.append(a)
            i += 1
        sdnn = math.sqrt(sum(ppisum)/(i-1))
        i = 0
        p = 0
        
        for o in range((len(ppi))-1):
            a = (ppi[o+1]-ppi[o]) **2
            p += a
            i += 1
        rmssd = math.sqrt(p/(i-1))
        time= self.rtc.datetime()
        date = str(time[0]) + "/" + str(time[1]) + "/" + str(time[2]) + " " + str(time[4]) + "." + str(time[5])
        timestamp = date
        
        mesurment = {
            "mean_hr":mean_hr,
            "mean_ppi": mean_ppi,
            "rmssd": rmssd,
            "sdnn": sdnn,
            "timestamp": timestamp
            }
        return mesurment
    
analysis = Analysis()
mesure = analysis.calculate()
print(mesure)