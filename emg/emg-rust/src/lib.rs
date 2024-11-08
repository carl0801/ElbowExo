use ndarray::{Array1, Array2, s, concatenate, Axis};
use numpy::{PyArray1, PyReadonlyArray1, PyReadonlyArray2, ToPyArray};
use pyo3::prelude::*;


/// Pad The signal with symmetric padding
fn pad_reflect(signal: &Array1<f64>, n_pad: usize) -> Array1<f64> {
    // Check if the signal length is less than n_pad
    if n_pad > signal.len() {
        // If signal is too short, pad with the first and last elements
        let first_value = signal[0];
        let last_value = signal[signal.len() - 1];

        let start_pad = Array1::from_elem(n_pad, first_value);
        let end_pad = Array1::from_elem(n_pad, last_value);

        // Concatenate padding and signal
        return concatenate![Axis(0), start_pad.view(), signal.view(), end_pad.view()];
    }

    // Get the first n_pad elements in reverse order for start padding
    let start_pad = signal.slice(s![..n_pad;-1]).to_owned();
    
    // Get the last n_pad elements in reverse order for end padding
    let end_pad = signal.slice(s![(signal.len() - n_pad)..;-1]).to_owned();
    
    // Concatenate padding and signal
    concatenate![Axis(0), start_pad.view(), signal.view(), end_pad.view()]
}


/// Initialize the zi state for the SOS filter based on the steady-state assumption.
/// This function estimates zi so that the filter output stabilizes quickly.
fn initialize_zi(sos_matrix: &Array2<f64>, x0: f64) -> Array2<f64> {
    let n_sections = sos_matrix.nrows();
    let mut zi = Array2::<f64>::zeros((n_sections, 2));

    for section_idx in 0..n_sections {
        let section = sos_matrix.row(section_idx);
        let (_b0, b1, b2, _a0, a1, a2) = (section[0], section[1], section[2], section[3], section[4], section[5]);

        // Calculate the initial state zi for this section
        let zi_0 = (b1 * x0 - a1 * x0) / (1.0 - a1);
        let zi_1 = (b2 * x0 - a2 * x0) / (1.0 - a2);

        // Set initial conditions
        zi[[section_idx, 0]] = zi_0;
        zi[[section_idx, 1]] = zi_1;
    }
    
    zi
}


/// Apply SOS filter forwards over the signal x.
fn sosfilt(x: &Array1<f64>, sos_matrix: &Array2<f64>, mut zi: Array2<f64>) -> Array1<f64> {
    let n_sections = sos_matrix.nrows();
    let mut y = Array1::<f64>::zeros(x.len());
    
    for (n, &x_n) in x.iter().enumerate() {
        let mut x_n = x_n;
        for section_idx in 0..n_sections {
            let section = sos_matrix.row(section_idx);
            let (b0, b1, b2, _a0, a1, a2) = (section[0], section[1], section[2], section[3], section[4], section[5]);
            
            // Apply direct form II transposed structure
            let y_n = b0 * x_n + zi[[section_idx, 0]];
            zi[[section_idx, 0]] = b1 * x_n - a1 * y_n + zi[[section_idx, 1]];
            zi[[section_idx, 1]] = b2 * x_n - a2 * y_n;


            // Update input for the next section
            x_n = y_n;
        }
        y[n] = x_n;
    }
    
    y
}

// Implement sosfiltfilt using sosfilt and initialize_zi
fn sosfiltfilt(x: &Array1<f64>, sos_matrix: &Array2<f64>) -> Array1<f64> {
    let n_pad = 100; // Number of samples to pad, adjust as needed
    let x_padded = pad_reflect(x, n_pad); // Pad the input signal

    // Initialize `zi` for forward pass with the first value of `x`
    let zi_forward = initialize_zi(&sos_matrix, x_padded[0]);
    
    // Apply the filter forwards
    let y_forward = sosfilt(&x_padded, &sos_matrix, zi_forward.clone());
    
    // Reverse the signal for the backward pass
    let y_reversed = y_forward.slice(s![..;-1]).to_owned();
    
    // Initialize `zi` for backward pass with the first value of reversed signal
    let zi_backward = initialize_zi(&sos_matrix, y_reversed[0]);
    
    // Apply the filter backwards
    let y_backward = sosfilt(&y_reversed, &sos_matrix, zi_backward.clone());
    
    // Reverse the signal back to original order
    let y_final = y_backward.slice(s![..;-1]).to_owned();
    y_final.slice(s![n_pad..(y_final.len() - n_pad)]).to_owned() // Remove padding
}


/// Python wrapper for sosfiltfilt
#[pyfunction]
#[pyo3(name = "sosfiltfilt")]
fn sosfiltfilt_python<'a>(
    py: Python<'a>,
    sos_matrix: PyReadonlyArray2<'a, f64>, 
    x: PyReadonlyArray1<'a, f64>
) -> PyResult<Bound<'a, PyArray1<f64>>> {

    // Convert PyReadonlyArray to ndarray ArrayView for processing
    let x = x.as_array();
    let sos_matrix = sos_matrix.as_array();
    let x_owned = x.to_owned();
    let sos_matrix_owned = sos_matrix.to_owned();

    // Apply the filter sosfiltfilt()
    let y_filtfilt = sosfiltfilt(&x_owned, &sos_matrix_owned);
    
    // Convert the result back to a Python array
    let result = y_filtfilt.to_pyarray_bound(py);
    Ok(result)
}


// A Python module implemented in Rust.
#[pymodule]
fn emg_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(sosfiltfilt_python, m)?)?;
    Ok(())
}