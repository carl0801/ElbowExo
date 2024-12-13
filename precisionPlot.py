import matplotlib.pyplot as plt
import numpy as np

# Define the data for the experiment
def get_data():
    # Fixed data for two runs
    target_degrees = [45, 90, 120, 90, 120, 45, 120, 90, 45]  # Ordered target degrees
    correct_steps = [614, 1372, 1867]  # Correct steps corresponding to degrees

    # Data for two runs
    actual_steps_data_run1 = [643, 1395, 1872, 1360, 1865, 616, 1845, 1367, 620]
    actual_steps_data_run2 = [614, 1371, 1864, 1372, 1864, 613, 1873, 1368, 616]

    return correct_steps, target_degrees, actual_steps_data_run1, actual_steps_data_run2

# Perform calculations and create plots
def analyze_and_plot(target_degrees, correct_steps, actual_steps_data_run1, actual_steps_data_run2):
    differences_run1 = []
    differences_run2 = []

    # Create a lookup table for degrees per step
    deg_per_step_lookup = {deg: deg / step for deg, step in zip([45, 90, 120], correct_steps)}

    # Calculate differences for Run 1
    for target_deg, actual_step in zip(target_degrees, actual_steps_data_run1):
        deg_per_step = deg_per_step_lookup[target_deg]  # Correct degrees per step
        actual_deg = deg_per_step * actual_step  # Actual degree
        diff = actual_deg - target_deg  # Difference from target
        differences_run1.append(diff)

    # Calculate differences for Run 2
    for target_deg, actual_step in zip(target_degrees, actual_steps_data_run2):
        deg_per_step = deg_per_step_lookup[target_deg]  # Correct degrees per step
        actual_deg = deg_per_step * actual_step  # Actual degree
        diff = actual_deg - target_deg  # Difference from target
        differences_run2.append(diff)

    # Plotting
    plt.figure(figsize=(8, 3))

    # Box Plot
    plt.boxplot([differences_run1, differences_run2], vert=False, patch_artist=True, labels=["Run 1", "Run 2"])
    plt.title('Box Plot of Differences')
    plt.xlabel('Difference (deg)')

    plt.tight_layout()
    plt.savefig('boxPlot.png')
    plt.show()

# Main execution
def main():
    correct_steps, target_degrees, actual_steps_data_run1, actual_steps_data_run2 = get_data()
    analyze_and_plot(target_degrees, correct_steps, actual_steps_data_run1, actual_steps_data_run2)

if __name__ == "__main__":
    main()
