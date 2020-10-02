import os
import sounddevice as sd
from scipy.signal import butter, lfilter, welch, chirp
from scipy.io import wavfile
import numpy as np
import matplotlib.pyplot as plt
from app.productiontest.constants import TEST_RESULTS_FOLDER


def _butter_bandpass(lowcut, highcut, fs, order=5):
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def _butter_bandpass_filter(data, lowcut, highcut, fs, order=5):
    b, a = _butter_bandpass(lowcut, highcut, fs, order=order)
    y = lfilter(b, a, data)
    return y


class SpeakerTest(object):

    def __init__(self, name, fs=44100, duration=5):

        self.instrument_name = name
        self.instrument_device_num = -1
        self.mic_device_num = -1

        # time domain
        self.fs = fs
        self.duration = duration
        self.time = None
        self.recording = None
        self.filtered_recording = None
        self.generated_signal = None

        # frequency domain
        self.freq = None
        self.rec_psd = None
        self.sig_psd = None

        # check to see if mic and instrument are connected
        self._determine_device_numbers()

    def _determine_device_numbers(self):

        devices = sd.query_devices()

        for ind, d in enumerate(devices):
            if 'mic' in d['name'].lower():
                self.mic_device_num = ind
            elif 'instrument1' in d['name'].lower():
                self.instrument_device_num = ind

        if self.instrument_device_num == -1:
            raise Exception('ERROR: {} not detected.'.format(self.instrument_name))

        if self.mic_device_num == -1:
            raise Exception('ERROR: Microphone not detected.')

    def generate_sine(self, sine_freq_hz=1000, npad=4096):
        """
        Generate a sine tone at the specified frequency.

        :param sine_freq_hz: float or int, frequency of sine in Hz, default = 1000 Hz
        :param npad: int, number of points for linear zero padding at signal edges, default = 4096 points
        :return: None, values go to self.time, self.generated_signal
        """
        self.time = np.arange(self.fs * self.duration) / self.fs
        self.generated_signal = np.sin(2 * np.pi * sine_freq_hz * self.time)

        pad_array = np.arange(npad) / float(npad)
        self.generated_signal[:npad] = pad_array * self.generated_signal[:npad]
        self.generated_signal[-npad:] = pad_array[::-1] * self.generated_signal[-npad:]

    def generate_chirp(self, f0=20, f1=20000, duration=20, method='logarithmic'):
        """
        Frequency-swept cosine generator.
        https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.signal.chirp.html

        :param f0: float, frequency at t0, default = 20 Hz
        :param f1: float, frequency at end of chirp, default = 20,000 hz
        :param duration: float, time at which f1 is specified, default = 20 s
        :param method: kind of frequency sweep, default = 'logarithmic'
        :return: None, values go to self.time, self.generated_signal
        """
        self.duration = duration
        self.time = np.arange(self.fs * self.duration) / self.fs
        self.generated_signal = chirp(self.time, f0, self.duration, f1, method=method)

    def record(self):
        """

        :return: None, values go to self.time
        """
        recording = sd.rec(self.duration * self.fs, samplerate=self.fs, channels=1, dtype='float64')
        sd.wait()
        self.recording = recording.reshape(len(recording), )
        self.rec_time = np.arange(len(self.recording)) / float(self.fs)

    def play_recording(self):
        if isinstance(self.recording, np.ndarray):
            sd.play(self.recording, self.fs, device=self.instrument_device_num)
            sd.wait()

    def play_generated_signal(self):
        if isinstance(self.generated_signal, np.ndarray):
            sd.play(self.generated_signal, self.fs, device=self.instrument_device_num)
            sd.wait()

    def play_and_record(self):

        input_stream = sd.InputStream(device=self.mic_device_num, channels=1, samplerate=self.fs)
        input_stream.start()

        sd.play(self.generated_signal, self.fs, device=self.instrument_device_num)
        recording = input_stream.read(len(self.generated_signal))[0]
        input_stream.stop()

        recording = recording.reshape(len(recording), )

        self.recording = recording
        self.filtered_recording = self._filter_recording(recording)

    def save_to_wav(self, sig_or_rec, filename=None):
        if sig_or_rec == 'recording':
            arr = self.recording
        elif sig_or_rec == 'signal':
            arr = self.generated_signal
        else:
            arr = None

        if isinstance(arr, np.ndarray):
            wavfile.write(filename, self.fs, arr)

    def _filter_recording(self, data, f_low=10, f_high=21000, filt_order=5, npad=4096):

        # copy recording
        prepped_recording = data.copy()

        # zero pad signal
        pad_array = np.arange(npad) / float(npad)
        prepped_recording[:npad] = pad_array * prepped_recording[:npad]
        prepped_recording[-npad:] = pad_array[::-1] * prepped_recording[-npad:]

        # filter time history
        prepped_recording = _butter_bandpass_filter(prepped_recording, f_low, f_high, self.fs, order=filt_order)

        return prepped_recording

    def audio_analysis(self, data_in, filter_time_history=False, nperseg=2**12, bandwidth_convert=False):

        data = data_in.copy()

        if filter_time_history:
            data = self._filter_recording(data, self.fs)

        # PSD
        f, psd = welch(data, self.fs, nperseg=nperseg)

        if bandwidth_convert:
            # convert to 1/12 octave band
            f_low, f_center, f_high = self._build_bandwidth()
            f, psd = self._bandwidth_convert(f, psd, f_low, f_center, f_high)

        return f, psd

    def calculate_thdn(self):

        if isinstance(self.rec_psd, np.ndarray) and isinstance(self.sig_psd, np.ndarray):

            # diff psds
            psd_diff = self.rec_psd - self.sig_psd

            noise_inds = np.where(psd_diff > 0)[0]

            return np.sqrt(np.sum(psd_diff[noise_inds] * np.mean(np.diff(self.freq[noise_inds]))))

    def plot_result(self, sig_or_rec, instrument=None, sn=None, figure_name=None):

        fig = plt.figure(dpi=100, figsize=(10, 8))
        if instrument and sn:
            title = '{} SN: {} Speaker Quality Test'.format(instrument, sn)
        else:
            title = 'Speaker Quality Test'
        fig.suptitle(title)

        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)

        if sig_or_rec == 'signal':
            data = self.generated_signal
            psd = self.sig_psd
            y_label = 'generated signal'
        elif sig_or_rec == 'filtered':
            data = self.filtered_recording
            psd = self.rec_psd
            y_label = 'filtered audio'
        else:
            data = self.recording
            psd = self.rec_psd
            y_label = 'recorded audio'

        time = np.arange(len(data)) / float(self.fs)

        ax1.plot(time, data)
        ax1.set_xlim(0, time[-1])
        ax1.set_xlabel('time (s)')
        ax1.set_ylabel(y_label)
        ax1.grid(which='both', axis='both')

        ax2.loglog(self.freq, psd)
        ax2.set_xlim(10, 20000)
        ax2.set_xlabel('freq (Hz)')
        ax2.set_ylabel('Power Spectral Density V^2/Hz')
        ax2.grid(which='both', axis='both')

        if figure_name:
            current_directory = os.path.dirname(os.path.realpath(__file__))
            top_level_directory = os.path.sep.join(current_directory.rstrip(os.path.sep).split(os.path.sep)[:-3])

            path = os.path.join(top_level_directory, TEST_RESULTS_FOLDER)

            if not os.path.isdir(path):
                os.makedirs(path)

            full_path = os.path.join(path, figure_name)
            plt.savefig(full_path)
            plt.close(fig)

    def plot_psds(self, instrument=None, sn=None, figure_name=None, thdn=None):
        fig = plt.figure(dpi=100, figsize=(10, 8))
        if instrument and sn:
            title = '{} SN: {} Input and Output PSDs'.format(instrument, sn)
        else:
            title = 'Input and Output PSDs'

        if thdn:
            title += '\nTHD + N: {}'.format(thdn)
        fig.suptitle(title)

        ax1 = fig.add_subplot(111)

        ax1.loglog(self.freq, self.sig_psd, self.freq, self.rec_psd)
        ax1.set_xlim(10, 20000)
        ax1.set_xlabel('freq (Hz)')
        ax1.set_ylabel('Power Spectral Density V^2/Hz')
        ax1.grid(which='both', axis='both')
        ax1.legend(['input signal', 'recorded audio'])

        if figure_name:
            current_directory = os.path.dirname(os.path.realpath(__file__))
            top_level_directory = os.path.sep.join(current_directory.rstrip(os.path.sep).split(os.path.sep)[:-3])

            path = os.path.join(top_level_directory, TEST_RESULTS_FOLDER)

            if not os.path.isdir(path):
                os.makedirs(path)

            full_path = os.path.join(path, figure_name)
            plt.savefig(full_path)
            plt.close(fig)

    @staticmethod
    def _build_bandwidth(f1=20.0, f2=21000.0, band=12):

        # octave band
        foct = np.array([f1])
        while foct[-1] < f2:
            foct = np.concatenate((foct, np.array([foct[-1] * 2.])))

        foct = foct[foct < f2]

        f_low = np.array([])
        for ind in range(1, len(foct)):
            f1 = foct[ind-1]
            f2 = foct[ind]
            step = (f2 - f1) / float(band)
            addition = np.arange(band) * step + f1
            f_low = np.concatenate((f_low, addition))

        f_high = np.concatenate((f_low[1:], np.array([foct[-1]])))

        f_center = (f_low + f_high) / 2

        return f_low, f_center, f_high

    def _bandwidth_convert(self, f_in, psd_in, f_low, f_center, f_high):

        # drop values below 20 Hz
        f_in = f_in[f_in > 20]
        psd_in = psd_in[-len(f_in):]

        # find index of f_band where step in f_in is great than 2 times step in f_band
        cross_ind = np.where(np.diff(f_center) > np.mean(np.diff(f_in)) * 2)[0][0]

        # use the start of the welch result for the converted output
        f_out = f_in[:cross_ind].tolist()
        psd_out = psd_in[:cross_ind].tolist()

        band_ind = np.where(f_low < f_in[cross_ind])[0][-1]
        f_low[band_ind] = f_out[-1]

        for ind in range(band_ind, len(f_center)):

            # find indices of f_in values between f_low[ind] and f_high[ind]
            l_ind = np.where(f_in > f_low[ind])[0][0]
            h_ind = np.where(f_in <= f_high[ind])[0][-1]

            avg_val = np.sum(psd_in[l_ind:h_ind+1]) / len(psd_in[l_ind:h_ind+1])

            psd_out.append(avg_val)
            f_out.append(f_center[ind])

        return np.array(f_out), np.array(psd_out)


def run_test(instrument_name):

    st = SpeakerTest(instrument_name)

    st.generate_sine(1000)
    # st.play_generated_signal()
    st.play_and_record()
    st.freq, st.sig_psd = st.audio_analysis(st.generated_signal)
    _, st.rec_psd = st.audio_analysis(st.filtered_recording)
    thdn = st.calculate_thdn()
    # print('THD+N = {}'.format(thdn))
    st.plot_psds(instrument=instrument_name, thdn=thdn)


instrument_name = 'Instrument1'
run_test(instrument_name)

