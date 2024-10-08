from itertools import product

import numpy as np
import pytest
from numpy.testing import assert_allclose
from scipy.signal import find_peaks

from stimuli.audio import SoundAM
from stimuli.audio.am import _check_frequency


def _assert_frequency(signal, sample_rate, fc, fm, method):
    """Check frequency content of the AM sound."""
    frequencies = np.fft.rfftfreq(signal.shape[0], 1 / sample_rate)
    fftval = np.abs(np.fft.rfft(signal, axis=0))
    height = 0.1 * np.max(fftval)
    peaks = find_peaks(fftval[:, 0], height=height)[0]
    peaks = peaks.astype(int)
    if method == "conventional":
        assert peaks.size == 3
        idx = np.argmax(fftval, axis=0)
        assert_allclose(frequencies[idx], fc)
        peaks = [elt for elt in peaks if elt not in idx]  # remove carrier from peaks
    elif method == "dsbsc":
        assert peaks.size == 2
        assert fc not in frequencies[peaks]
    assert_allclose(
        frequencies[peaks],
        np.array([fc - fm, fc + fm]),
    )


@pytest.mark.parametrize(
    ("fc", "fm", "method", "volume", "duration"),
    product((1000, 2000), (40, 100), ("dsbsc", "conventional"), (10, 100), (1, 5)),
)
def test_sound_am(fc, fm, method, volume, duration):
    """Test an amplitude-modulated sound."""
    sound = SoundAM(
        frequency_carrier=fc,
        frequency_modulation=fm,
        method=method,
        volume=volume,
        duration=duration,
    )
    assert sound.volume.ndim == 1
    assert all(sound.volume == volume)
    assert sound.duration == duration
    assert sound.times.size == int(sound.sample_rate * sound.duration)
    assert sound.signal.shape == (sound.times.size, 1)
    assert_allclose(np.max(np.abs(sound.signal)), volume / 100)
    assert sound.method == method
    assert sound._frequency_carrier == fc
    assert sound._frequency_modulation == fm
    _assert_frequency(sound.signal, sound.sample_rate, fc, fm, method)


@pytest.mark.parametrize("ftype", ["carrier", "modulation"])
def test_check_frequency(ftype):
    """Test validation of frequency."""
    _check_frequency(440, ftype)
    with pytest.raises(
        ValueError, match=f"The {ftype} frequency must be a strictly positive"
    ):
        _check_frequency(0, ftype)
    with pytest.raises(
        ValueError, match=f"The {ftype} frequency must be a strictly positive"
    ):
        _check_frequency(-440, ftype)
    with pytest.raises(TypeError, match="must be an instance of"):
        _check_frequency("440", ftype)
