from __future__ import print_function

import time
import sys
import math
import numpy as np
import scipy as sp
from threading import Thread
from scipy.integrate import simps
from time import sleep
from numpy.linalg import norm, qr
from scipy.signal import resample, butter, filtfilt

NUM_SAMPLES = 1024
NUM_DOWNSAMPLE = 128
SAMPLING_RATE = 32000.
MAX_FREQ = SAMPLING_RATE / 2
FREQ_SAMPLES = NUM_SAMPLES / 8
TIMESLICE = 1. / SAMPLING_RATE * NUM_SAMPLES * 1000.
NUM_BINS = 16
NUM_SLICES = math.ceil(10. * 1000. / TIMESLICE)
SUBS_GAIN = 10.

data = {'values': None}

def wthresh(a, thresh):
    #Soft wavelet threshold
    res = np.abs(a) - thresh
    return np.sign(a) * ((res > 0) * res)

#Default threshold of .03 is assumed to be for input in the range 0-1...
#original matlab had 8 out of 255, which is about .03 scaled to 0-1 range
def go_dec(X, thresh=.03, rank=5, power=0, tol=1e-3,
           max_iter=100, random_seed=0, verbose=True):
    m, n = X.shape
    if m < n:
        X = X.T
    m, n = X.shape
    L = X
    S = np.zeros(L.shape)
    itr = 0
    random_state = np.random.RandomState(random_seed)
    while True:
        Y2 = random_state.randn(n, rank)
        for i in range(power + 1):
            Y1 = np.dot(L, Y2)
            Y2 = np.dot(L.T, Y1)
        Q, R = qr(Y2)
        L_new = np.dot(np.dot(L, Q), Q.T)
        T = L - L_new + S
        L = L_new
        S = wthresh(T, thresh)
        T -= S
        err = norm(T.ravel(), 2)
        if (err < tol) or (itr >= max_iter):
            break
        L += T
        itr += 1
    #Is this even useful in soft GoDec? May be a display issue...
    G = X - L - S
    if m < n:
        L = L.T
        S = S.T
        G = G.T
    if verbose:
        print("Finished at iteration %d" % (itr))

    return L, S, G


def background_thread_worker(stream):
    X = np.zeros((NUM_DOWNSAMPLE, NUM_SLICES))
    L, S, G = False, False, False

    # Design the Butterworth filter
    N = 2  # Filter order
    Wn = 0.02  # Cutoff frequency
    b, a = butter(N, Wn, output='ba')

    while True:
        try:
            raw_data = np.fromstring(stream.read(NUM_SAMPLES), dtype=np.int16)
            signal = raw_data / 32768.0
            fft = sp.fft(signal)
            spectrum = abs(fft)[:int(NUM_SAMPLES / 2)]
            power = spectrum ** 2
            bins = simps(np.split(power, NUM_BINS))
            X = np.roll(X, shift=1, axis=1)
            #X[:, 0] = resample(signal * SUBS_GAIN, num=NUM_DOWNSAMPLE)
            X[:, 0] = filtfilt(b, a, resample(signal * SUBS_GAIN, num=NUM_DOWNSAMPLE))
            L, S, G = go_dec(X, rank=3, max_iter=25, verbose=False)
            low_rank = resample(L[:, -1], num=NUM_SAMPLES)
            sparse = resample(S[:, -1], num=NUM_SAMPLES)

            data['values'] = signal, spectrum, bins, low_rank, sparse

            #time.sleep(.125)
        except:
            print(sys.exc_info())
            continue


try:
    import pyaudio

    X = np.zeros((NUM_DOWNSAMPLE, NUM_SLICES))
    L, S, G = False, False, False

    def update_audio_data():
        global X
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=int(SAMPLING_RATE),
            input=True,
            frames_per_buffer=NUM_SAMPLES
        )

        thread = Thread(target=background_thread_worker, args=(stream,))
        thread.start()

except:
    print()
    print(" *** Pyaudio package not installed, using synthesized audio data ***")
    print()

    def fm_modulation(x, f_carrier = 220, f_mod =220, Ind_mod = 1):
        y = np.sin(2*np.pi*f_carrier*x + Ind_mod*np.sin(2*np.pi*f_mod*x))
        return y

    # These are basically picked out of a hat to show something vaguely interesting
    _t = np.arange(0, NUM_SAMPLES/SAMPLING_RATE, 1.0/SAMPLING_RATE)
    _f_carrier = 2000
    _f_mod = 1000
    _ind_mod = 1

    def update_audio_data():
        while True:
            # Generate FM signal with drifting carrier and mod frequencies
            global _f_carrier, _f_mod, _ind_mod
            _f_carrier = max([_f_carrier+np.random.randn()*50, 0])
            _f_mod = max([_f_mod+np.random.randn()*20, 0])
            _ind_mod = max([_ind_mod+np.random.randn()*0.1, 0])
            A = 0.4 + 0.05 * np.random.random()
            signal = A * fm_modulation(_t, _f_carrier, _f_mod, _ind_mod)

            fft = sp.fft(signal)
            spectrum = abs(fft)[:int(NUM_SAMPLES/2)]
            power = spectrum**2
            bins = simps(np.split(power, NUM_BINS))
            data['values'] = signal, spectrum, bins
            X = np.roll(X, shift=1, axis=1)
            #X[:, 0] = resample(signal * SUBS_GAIN, num=NUM_DOWNSAMPLE)
            X[:, 0] = filtfilt(b, a, resample(signal * SUBS_GAIN, num=NUM_DOWNSAMPLE))
            L, S, G = go_dec(X, rank=3, max_iter=100)
            low_rank = resample(L[:, -1], num=NUM_SAMPLES)
            sparse = resample(S[:, -1], num=NUM_SAMPLES)
            
            sleep(1.0/12)
