import numpy as np

def sos_filter_forward(x, sos_matrix, zi):
    """
    Apply SOS filter forwards over the signal x.
    """
    n_sections = sos_matrix.shape[0]
    y = np.zeros_like(x)
    
    for n in range(len(x)):
        x_n = x[n]
        for s in range(n_sections):
            b0, b1, b2, a0, a1, a2 = sos_matrix[s]
            
            # Apply direct form II transposed structure
            y_n = b0 * x_n + zi[s, 0]
            zi[s, 0] = b1 * x_n - a1 * y_n + zi[s, 1]
            zi[s, 1] = b2 * x_n - a2 * y_n
            
            # Update input for the next section
            x_n = y_n
        
        # Store the final output after all sections
        y[n] = y_n
    
    return y

def sosfiltfilt(sos_matrix, x):
    """
    Apply an SOS filter forwards and backwards to achieve zero-phase filtering.
    """
    # Initialize state memory for each section (zeros at start)
    n_sections = sos_matrix.shape[0]
    zi = np.zeros((n_sections, 2))
    
    # Forward pass
    y_forward = sos_filter_forward(x, sos_matrix, zi.copy())
    
    # Reverse the signal and apply forward filter again
    y_reverse = sos_filter_forward(y_forward[::-1], sos_matrix, zi.copy())
    
    # Reverse the result back
    y_filtfilt = y_reverse[::-1]
    
    return y_filtfilt

# Example usage
sos_matrix = np.array([
    [1.0, 0.61803, 1.0, 1.0, 0.60515, 0.95873],
    [1.0, -1.61803, 1.0, 1.0, -1.58430, 0.95873],
    [1.0, 1.0, 0.0, 1.0, 0.97915, 0.0]
])

# Sample signal
x = np.sin(2 * np.pi * 0.1 * np.arange(100))

# Apply filtfilt
y = sosfiltfilt(sos_matrix, x)

print("Filtered signal:", y)
