from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np
from matplotlib import pyplot as plt
from scipy.io import wavfile

from ..utils._checks import check_type, check_value, ensure_int, ensure_path
from ..utils._docs import copy_doc, fill_doc
from ..utils.logs import logger
from .backend import BACKENDS
from .backend._base import BaseBackend

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from matplotlib.axes import Axes
    from matplotlib.figure import Figure
    from numpy.typing import NDArray

    from ..time import BaseClock


@fill_doc
class BaseSound(ABC):
    """Base audio stimulus class.

    Parameters
    ----------
    %(audio_volume)s
    %(audio_duration)s
    %(audio_sample_rate)s
    %(audio_device)s
    %(audio_n_channels)s
    %(audio_backend)s
    %(audio_clock)s
    %(audio_kwargs)s
    """

    @abstractmethod
    def __init__(
        self,
        volume: float | Sequence[float],
        duration: float,
        sample_rate: int | None,
        device: int | None,
        n_channels: int = 1,
        *,
        backend: str,
        clock: BaseClock,
        **kwargs,
    ) -> None:
        check_type(backend, (str,), "backend")
        check_value(backend, BACKENDS, "backend")
        _check_duration(duration)
        self._duration = duration
        self._n_channels = ensure_int(n_channels, "n_channels")
        if self._n_channels < 1:
            raise ValueError(
                "The number of channels must be at least 1. Provided "
                f"'{self._n_channels}' is invalid."
            )
        self._volume = _ensure_volume(volume, self._n_channels)
        # the arguments sample_rate, device, clock, and **kwargs are checked in
        # the backend initialization.
        self._backend_kwargs = kwargs
        self._backend = BACKENDS[backend](device, sample_rate, clock=clock)
        self._set_times()
        self._set_signal()

    def _set_times(self) -> None:
        """Set the timestamp array."""
        self._times = np.linspace(
            0,
            self.duration,
            int(self.duration * self.sample_rate),
            endpoint=False,
            dtype=np.float32,
        )

    @abstractmethod
    def _set_signal(self, signal: NDArray) -> None:
        """Set the signal array."""
        signal = np.vstack([signal] * self._n_channels).T
        assert self._volume.ndim == 1  # sanity-check
        assert self._volume.size == self._n_channels  # sanity-check
        signal = np.ascontiguousarray(signal) * self._volume / 100
        signal = signal.astype(np.float32)  # sanity-check
        self._signal = signal

    @copy_doc(BaseBackend.play)
    def play(self, when: float | None = None) -> None:
        self._backend.play(when=when)

    def plot(self) -> tuple[Figure, Axes]:
        """Plot the audio signal waveform."""
        f, ax = plt.subplots(1, 1, layout="constrained")
        ax.plot(self.times, self.signal)
        ax.set_xlabel("Time [s]")
        ax.set_ylabel("Amplitude")
        ax.set_title(repr(self))
        return f, ax

    def save(self, fname: str | Path, *, overwrite: bool = False) -> None:
        """Save the audio stimulus to a WAV file.

        The saving is handled by :func:`scipy.io.wavfile.write`.

        Parameters
        ----------
        fname : str | Path
            Path to the output file. The extension should be ``'.wav'``.
        overwrite : bool
            If True, existing files are overwritten.
        """
        fname = ensure_path(fname, must_exist=False)
        if fname.suffix != ".wav":
            raise ValueError("The file extension must be '.wav'.")
        if overwrite is False and fname.exists():
            raise FileExistsError(
                f"The file '{fname}' already exists. Set 'overwrite' to True."
            )
        fname.parent.mkdir(parents=True, exist_ok=True)
        logger.debug("Saving sound to %s.", fname)
        wavfile.write(fname, self.sample_rate, self.signal)

    @copy_doc(BaseBackend.stop)
    def stop(self) -> None:
        self._backend.stop()

    @property
    def duration(self) -> float:
        """The duration of the audio stimulus.

        :type: :class:`float`
        """
        return self._duration

    @duration.setter
    def duration(self, duration: float):
        logger.debug("Setting 'duration' to %s [s].", duration)
        _check_duration(duration)
        self._duration = duration
        self._set_times()
        self._set_signal()

    @property
    def sample_rate(self) -> int:
        """The sample rate of the audio stimulus.

        :type: :class:`int`
        """
        return self._backend.sample_rate

    @property
    def signal(self) -> NDArray[np.float32]:
        """The audio signal.

        :type: array of shape (n_samples, n_channels)
        """
        return self._signal

    @property
    def times(self) -> NDArray[np.float32]:
        """The time array of the audio stimulus.

        :type: array of shape (n_samples,)
        """
        return self._times

    @property
    def volume(self) -> NDArray[np.float32]:
        """The volume of the audio stimulus per channel given as a percentage.

        :type: array of shape (n_channels,)
        """
        return self._volume

    @volume.setter
    def volume(self, volume: float | Sequence[float]) -> None:
        logger.debug("Setting 'volume' to %s [%].", volume)
        self._volume = _ensure_volume(volume, self._n_channels)
        self._set_signal()

    @property
    def _signal(self) -> NDArray[np.float32]:
        """The audio signal."""
        return self._signal_array

    @_signal.setter
    def _signal(self, signal: NDArray[np.float32]) -> None:
        self._backend.close()  # np-op if already closed
        self._signal_array = signal
        self._backend.initialize(self._signal_array, **self._backend_kwargs)


def _ensure_volume(volume: float | Sequence[float], n_channels: int) -> None:
    """Check that the volume is valid."""
    if isinstance(volume, (float | int)):
        volume = np.full(n_channels, volume, dtype=np.float32)
    check_type(volume, ("array-like",), "volume")
    volume = np.asarray(volume, dtype=np.float32)
    if volume.ndim != 1:
        raise ValueError(
            "The volume must be a single value or a sequence of values. Provided "
            f"'{volume}' is invalid."
        )
    if volume.size != n_channels:
        raise ValueError(
            "The number of volume values must match the number of channels. "
            f"Provided '{volume.size}' values for '{n_channels}' channels."
        )
    if np.any(volume < 0) or np.any(100 < volume):
        raise ValueError(
            "The volume must be a percentage between 0 and 100. Provided "
            f"'{volume}' is invalid."
        )
    return np.asarray(volume, dtype=np.float32)


def _check_duration(duration: float) -> None:
    """Check if the duration is valid."""
    check_type(duration, ("numeric",), "duration")
    if duration <= 0:
        raise ValueError(
            "The argument 'duration' must be a strictly positive number defining "
            f"the length of the sound in seconds. Provided '{duration}' is invalid."
        )
