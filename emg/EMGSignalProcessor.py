import numpy as np
from scipy.signal import butter, sosfiltfilt

def butter_bandpass(lowcut, highcut, fs, order=4):
    sos = butter(order, [lowcut, highcut], btype='bandpass', fs=fs, output='sos')
    return sos

def notch_filter(freq, fs, order=4):
    sos  = butter(order, [freq-1.0, freq+1.0], btype='bandstop', fs=fs, output='sos')
    return sos

def generate_filter(fs=650, lowcut=20.0, highcut=250.0, notch_freq=50.0):
    # butterworth bandpass filter
    sos_b = butter_bandpass(lowcut, highcut, fs)
    # notch filter
    sos_n = notch_filter(notch_freq, fs)
    return [sos_b, sos_n]

def run_batch(sensor1, sensor2, coeff, multiplier=3.0, threshold=5.0, window_size=300):
    """
    Filter the EMG signals from two sensors, combine them, apply a threshold and then
    take the moving average.

    Parameters
    ----------
    sensor1 : array
        The data from sensor 1
    sensor2 : array
        The data from sensor 2
    coeff : list
        The coefficients for the filter (a list of 2, (x, 6) shaped arrays)
    multiplier : float
        The multiplier for the second sensor
    threshold : float
        The minimum absolute value of the data
    window_size : int
        The size of the window for the moving average

    Returns
    -------
    filtered_data : array
        The filtered data
    """
    # Bandpass filter between 20 Hz and 250 Hz
    filtered_sensor1 = sosfiltfilt(coeff[0], sensor1)
    filtered_sensor2 = sosfiltfilt(coeff[0], sensor2)
    # Notch filter around 50 Hz
    filtered_sensor1 = sosfiltfilt(coeff[1], filtered_sensor1)
    filtered_sensor2 = sosfiltfilt(coeff[1], filtered_sensor2)
    # Abs
    filtered_sensor1 = np.abs(filtered_sensor1)
    filtered_sensor2 = np.abs(filtered_sensor2)
    # Combine the sensors
    combined_sensor = filtered_sensor1 - multiplier * filtered_sensor2
    # Threshold
    combined_sensor = np.where(np.abs(combined_sensor) > threshold, combined_sensor, 0)
    # Moving average
    combined_sensor = np.convolve(combined_sensor, np.ones(window_size)/window_size, mode='same')

    return combined_sensor



filter = generate_filter(fs=650)
print(filter[0].shape)
print(filter[1].shape)







def sosfilt(sos, x, axis=-1, zi=None):
    """
    Filter data along one dimension using cascaded second-order sections.

    Filter a data sequence, `x`, using a digital IIR filter defined by
    `sos`.

    Parameters
    ----------
    sos : array_like
        Array of second-order filter coefficients, must have shape
        ``(n_sections, 6)``. Each row corresponds to a second-order
        section, with the first three columns providing the numerator
        coefficients and the last three providing the denominator
        coefficients.
    x : array_like
        An N-dimensional input array.
    axis : int, optional
        The axis of the input data array along which to apply the
        linear filter. The filter is applied to each subarray along
        this axis.  Default is -1.
    zi : array_like, optional
        Initial conditions for the cascaded filter delays.  It is a (at
        least 2D) vector of shape ``(n_sections, ..., 2, ...)``, where
        ``..., 2, ...`` denotes the shape of `x`, but with ``x.shape[axis]``
        replaced by 2.  If `zi` is None or is not given then initial rest
        (i.e. all zeros) is assumed.
        Note that these initial conditions are *not* the same as the initial
        conditions given by `lfiltic` or `lfilter_zi`.

    Returns
    -------
    y : ndarray
        The output of the digital filter.
    zf : ndarray, optional
        If `zi` is None, this is not returned, otherwise, `zf` holds the
        final filter delay values.

    See Also
    --------
    zpk2sos, sos2zpk, sosfilt_zi, sosfiltfilt, sosfreqz

    Notes
    -----
    The filter function is implemented as a series of second-order filters
    with direct-form II transposed structure. It is designed to minimize
    numerical precision errors for high-order filters.

    .. versionadded:: 0.16.0

    Examples
    --------
    Plot a 13th-order filter's impulse response using both `lfilter` and
    `sosfilt`, showing the instability that results from trying to do a
    13th-order filter in a single stage (the numerical error pushes some poles
    outside of the unit circle):

    >>> import matplotlib.pyplot as plt
    >>> from scipy import signal
    >>> b, a = signal.ellip(13, 0.009, 80, 0.05, output='ba')
    >>> sos = signal.ellip(13, 0.009, 80, 0.05, output='sos')
    >>> x = signal.unit_impulse(700)
    >>> y_tf = signal.lfilter(b, a, x)
    >>> y_sos = signal.sosfilt(sos, x)
    >>> plt.plot(y_tf, 'r', label='TF')
    >>> plt.plot(y_sos, 'k', label='SOS')
    >>> plt.legend(loc='best')
    >>> plt.show()

    """
    x = _validate_x(x)
    sos, n_sections = _validate_sos(sos)
    x_zi_shape = list(x.shape)
    x_zi_shape[axis] = 2
    x_zi_shape = tuple([n_sections] + x_zi_shape)
    inputs = [sos, x]
    if zi is not None:
        inputs.append(np.asarray(zi))
    dtype = np.result_type(*inputs)
    if dtype.char not in 'fdgFDGO':
        raise NotImplementedError("input type '%s' not supported" % dtype)
    if zi is not None:
        zi = np.array(zi, dtype)  # make a copy so that we can operate in place
        if zi.shape != x_zi_shape:
            raise ValueError('Invalid zi shape. With axis=%r, an input with '
                             'shape %r, and an sos array with %d sections, zi '
                             'must have shape %r, got %r.' %
                             (axis, x.shape, n_sections, x_zi_shape, zi.shape))
        return_zi = True
    else:
        zi = np.zeros(x_zi_shape, dtype=dtype)
        return_zi = False
    axis = axis % x.ndim  # make positive
    x = np.moveaxis(x, axis, -1)
    zi = np.moveaxis(zi, [0, axis + 1], [-2, -1])
    x_shape, zi_shape = x.shape, zi.shape
    x = np.reshape(x, (-1, x.shape[-1]))
    x = np.array(x, dtype, order='C')  # make a copy, can modify in place
    zi = np.ascontiguousarray(np.reshape(zi, (-1, n_sections, 2)))
    sos = sos.astype(dtype, copy=False)
    _sosfilt(sos, x, zi)
    x.shape = x_shape
    x = np.moveaxis(x, -1, axis)
    if return_zi:
        zi.shape = zi_shape
        zi = np.moveaxis(zi, [-2, -1], [0, axis + 1])
        out = (x, zi)
    else:
        out = x
    return out


def sosfiltfilt(sos, x, axis=-1, padtype='odd', padlen=None):
    """
    A forward-backward digital filter using cascaded second-order sections.

    See `filtfilt` for more complete information about this method.

    Parameters
    ----------
    sos : array_like
        Array of second-order filter coefficients, must have shape
        ``(n_sections, 6)``. Each row corresponds to a second-order
        section, with the first three columns providing the numerator
        coefficients and the last three providing the denominator
        coefficients.
    x : array_like
        The array of data to be filtered.
    axis : int, optional
        The axis of `x` to which the filter is applied.
        Default is -1.
    padtype : str or None, optional
        Must be 'odd', 'even', 'constant', or None.  This determines the
        type of extension to use for the padded signal to which the filter
        is applied.  If `padtype` is None, no padding is used.  The default
        is 'odd'.
    padlen : int or None, optional
        The number of elements by which to extend `x` at both ends of
        `axis` before applying the filter.  This value must be less than
        ``x.shape[axis] - 1``.  ``padlen=0`` implies no padding.
        The default value is::

            3 * (2 * len(sos) + 1 - min((sos[:, 2] == 0).sum(),
                                        (sos[:, 5] == 0).sum()))

        The extra subtraction at the end attempts to compensate for poles
        and zeros at the origin (e.g. for odd-order filters) to yield
        equivalent estimates of `padlen` to those of `filtfilt` for
        second-order section filters built with `scipy.signal` functions.

    Returns
    -------
    y : ndarray
        The filtered output with the same shape as `x`.

    See Also
    --------
    filtfilt, sosfilt, sosfilt_zi, sosfreqz

    Notes
    -----
    .. versionadded:: 0.18.0

    Examples
    --------
    >>> import numpy as np
    >>> from scipy.signal import sosfiltfilt, butter
    >>> import matplotlib.pyplot as plt
    >>> rng = np.random.default_rng()

    Create an interesting signal to filter.

    >>> n = 201
    >>> t = np.linspace(0, 1, n)
    >>> x = 1 + (t < 0.5) - 0.25*t**2 + 0.05*rng.standard_normal(n)

    Create a lowpass Butterworth filter, and use it to filter `x`.

    >>> sos = butter(4, 0.125, output='sos')
    >>> y = sosfiltfilt(sos, x)

    For comparison, apply an 8th order filter using `sosfilt`.  The filter
    is initialized using the mean of the first four values of `x`.

    >>> from scipy.signal import sosfilt, sosfilt_zi
    >>> sos8 = butter(8, 0.125, output='sos')
    >>> zi = x[:4].mean() * sosfilt_zi(sos8)
    >>> y2, zo = sosfilt(sos8, x, zi=zi)

    Plot the results.  Note that the phase of `y` matches the input, while
    `y2` has a significant phase delay.

    >>> plt.plot(t, x, alpha=0.5, label='x(t)')
    >>> plt.plot(t, y, label='y(t)')
    >>> plt.plot(t, y2, label='y2(t)')
    >>> plt.legend(framealpha=1, shadow=True)
    >>> plt.grid(alpha=0.25)
    >>> plt.xlabel('t')
    >>> plt.show()

    """
    sos, n_sections = _validate_sos(sos)
    x = _validate_x(x)

    # `method` is "pad"...
    ntaps = 2 * n_sections + 1
    ntaps -= min((sos[:, 2] == 0).sum(), (sos[:, 5] == 0).sum())
    edge, ext = _validate_pad(padtype, padlen, x, axis,
                              ntaps=ntaps)

    # These steps follow the same form as filtfilt with modifications
    zi = sosfilt_zi(sos)  # shape (n_sections, 2) --> (n_sections, ..., 2, ...)
    zi_shape = [1] * x.ndim
    zi_shape[axis] = 2
    zi.shape = [n_sections] + zi_shape
    x_0 = axis_slice(ext, stop=1, axis=axis)
    (y, zf) = sosfilt(sos, ext, axis=axis, zi=zi * x_0)
    y_0 = axis_slice(y, start=-1, axis=axis)
    (y, zf) = sosfilt(sos, axis_reverse(y, axis=axis), axis=axis, zi=zi * y_0)
    y = axis_reverse(y, axis=axis)
    if edge > 0:
        y = axis_slice(y, start=edge, stop=-edge, axis=axis)
    return y