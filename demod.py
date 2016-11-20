
from rtlsdr import RtlSdr
import numpy as np
import scipy as sp
import scipy.signal
from scipy.fftpack import fft, fftfreq, fftshift
import matplotlib.pyplot as plt
import time # time.clock() has microsec resolution on at least Windows and the RPi

def iq2complex(b):
    t = time.clock()
    b_np = np.ctypeslib.as_array(b)
    iq = np.empty(len(b)//2, np.complex64)
    # Use slicing to get the 8-bit I and Q samples from the input
    iq.real, iq.imag = b_np[::2], b_np[1::2]
    # Scale to -1 to 1
    iq /= 256
    iq -= (0.5 + 0.5j)
    #print("iq2complex time: %f" % (time.clock()-t))
    return iq

def my_decimate(s, q, T, N):
    t = time.clock() # clock has microsec resolution on Windows and the RPi
    n = 15 # 30 # default order ref https://github.com/scipy/scipy/blob/14686dc8b8c2df11caa10ca598ac52d889b8ad09/scipy/signal/signaltools.py
    b, a = sp.signal.firwin(n+1, 1. / q, window='hamming'), 1.
    #print("Decimate filter creation time: %f" % (time.clock()-t))

    t = time.clock() # clock has microsec resolution on Windows and the RPi
    f = sp.signal.lfilter(b, a, s)
    d = f[::q], T * q, N // q
    print("Decimate time: %f" % (time.clock()-t))
    return d

    #t = time.clock()
    #d = sp.signal.decimate(s, q, ftype='fir'), T * q, N // q
    #print("Decimate time: %f" % (time.clock()-t))
    return d

def lowpass(s):
    t = time.clock()
    b, a = sp.signal.firwin(20, 7.5/32.0, window='blackman'), 1.
    #print("Lowpass creation time: %f" % (time.clock()-t))
    t = time.clock()
    f = sp.signal.lfilter(b, a, s)
    #print("Lowpass filter time: %f" % (time.clock()-t))
    return f


# sample spacing
T = 1. / 2.048e6
# number of signal points
N = 204800 # 0.1 s at sample freq 2.048 MHz

sdr = RtlSdr()

# configure device
sdr.sample_rate = 1./T # 2.048e6  # Hz
print("Sample rate %d" % sdr.sample_rate)
sdr.center_freq = 110.1e6     # Hz
sdr.gain = 20 #'auto'

def process(cmd):
    if "center_freq" in cmd:
        print("Setting new center_freq", cmd["center_freq"])
        sdr.center_freq = cmd.get("center_freq")
        print("New center_freq:", sdr.center_freq)
    if "gain" in cmd:
        print("Setting new gain", cmd["gain"])
        sdr.gain = cmd.get("gain")
        print("New gain:", sdr.gain)

def demod(N, T):
    raw = sdr.read_bytes(N*2)
    y = iq2complex(raw)
    iny = y[0:N//100] # speeds up spectrum calculation and size (but reduces spectral resolution to N*T*100 = 1 kHz) 
    xrf = fftshift(fftfreq(len(iny), T))
    yrf = 20*np.log10(fftshift(1/len(iny)*abs(fft(iny))))
    
    y, T, N = my_decimate(y, 8, T, N)
    y, T, N = my_decimate(y, 4, T, N)
    y = lowpass(y)
    x = np.linspace(0.0, N * T, N)
    y = abs(y)
    yf = 1/N*fft(y)
    rf = abs(yf[0])
    mod90 = (abs(yf[90//10]) + abs(yf[len(yf)-90//10]))/rf*100
    mod150 = (abs(yf[150//10]) + abs(yf[len(yf)-150//10]))/rf*100
    xf = fftshift(fftfreq(len(y), T))
    yf = fftshift(yf)

    print("N=%d, rf=%.1f, mod90=%.1f, mod150=%.1f, ddm=%.2f, sdm=%.2f" % (N, rf, mod90, mod150, mod150-mod90, mod150+mod90))

    return {
        'center_freq': sdr.center_freq,
        'gain': sdr.gain,
        'rf': rf,
        'mod90': mod90,
        'mod150': mod150,
        'lf-timesignal': np.round(y, decimals=5).tolist(),
        'lf-spectrum': np.round(np.abs(yf), decimals=5).tolist(),
        'lf-xf': xf.tolist(),
        'lf-sps': 1/T,
        'rf-spectrum': yrf.tolist(),
        'rf-xf': xrf.tolist(),
        'rfi-timesignal': iny.real.tolist(),
        'rfq-timesignal': iny.imag.tolist(),
    }
