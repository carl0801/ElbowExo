use pyo3::prelude::*;
use rayon::prelude::*;
use std::simd::{f64x4}; // SIMD for 4 f64 values

#[pyfunction]
fn fir_filter(input: Vec<f64>, coefficients: Vec<f64>) -> PyResult<Vec<f64>> {
    let n = input.len();
    let filter_len = coefficients.len();
    let mut output = vec![0.0; n];

    // Process the input in parallel
    let chunk_size = n / rayon::current_num_threads(); // Divide input for each thread

    // Parallel processing using SIMD
    input
        .par_chunks(chunk_size)
        .enumerate()
        .for_each(|(chunk_index, chunk)| {
            let mut local_output = vec![0.0; chunk.len()];

            for i in 0..chunk.len() {
                let mut acc = 0.0;

                // SIMD processing of coefficients
                for j in (0..filter_len).step_by(4) {
                    // Use SIMD only if there are enough input values
                    if i >= j + 4 { // Ensure we have enough values to process
                        let input_chunk = f64x4::from_slice_unaligned(&input[(chunk_index * chunk_size) + i - j..]);
                        let coeff_chunk = f64x4::from_slice_unaligned(&coefficients[j..]);
                        acc += (input_chunk * coeff_chunk).horizontal_sum();
                    } else {
                        // Fallback to scalar processing if not enough data
                        acc += coefficients[j] * input[(chunk_index * chunk_size) + i - j];
                    }
                }
                local_output[i] = acc;
            }

            // Store results in the main output vector
            output[chunk_index * chunk_size..][..local_output.len()].copy_from_slice(&local_output);
        });

    Ok(output)
}

/// A Python module implemented in Rust.
#[pymodule]
fn my_project(m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fir_filter, m)?)?;
    Ok(())
}
