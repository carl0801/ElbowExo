import matplotlib.pyplot as plt
import numpy as np
import scipy.stats as stats

# Define the data for the experiment
def get_data():
    # target_deg = [45, 90, 120, 90, 120, 45, 120, 90, 45] 
    # Test 7.1 and 7.2
    # correct_steps = [614, 1372, 1867] 
    steps_test1 = [643, 1395, 1872, 1360, 1865, 616, 1845, 1367, 620]
    steps_test2 = [614, 1371, 1864, 1372, 1864, 613, 1873, 1368, 616]
    target_steps1 = [614, 1372, 1867, 1372, 1867, 614, 1867, 1372, 614]
    
    # Test 7.3
    # correct_steps = [412, 831, 1322]
    steps_test3 = [435, 1100, 1540, 1045, 1600, 430, 1608, 1048, 415]
    target_steps3 = [412, 831, 1322, 831, 1322, 412, 1322, 831, 412]

    return target_steps1, target_steps3, steps_test1, steps_test2, steps_test3

def steps_to_degrees(steps):
    degrees_per_step = 0.062
    steps = np.array(steps)
    return steps * degrees_per_step

# Perform calculations and create plots
def analyze_and_plot(target_steps1, target_steps3, steps_test1, steps_test2, steps_test3):
    # Calculate differences for Test 7.1
    differences_test1 = steps_to_degrees(steps_test1) - steps_to_degrees(target_steps1)
    # Calculate differences for Test 7.2
    differences_test2 = steps_to_degrees(steps_test2) - steps_to_degrees(target_steps1)
    # Calculate differences for Test 7.3
    differences_test3 = steps_to_degrees(steps_test3) - steps_to_degrees(target_steps3)
    

    # Plotting
    plt.figure(figsize=(8, 3))

    # Box Plot
    plt.boxplot([differences_test1, differences_test2], vert=False, patch_artist=True, labels=["Test 7.1", "Test 7.2"])
    plt.xlabel('Difference (deg)')

    plt.tight_layout()
    plt.savefig('boxPlotTest_7.1-2.png')

    # Plotting
    plt.figure(figsize=(8, 2))

    # Box Plot
    plt.boxplot([differences_test3], vert=False, patch_artist=True, labels=["Test 7.3"])
    plt.xlabel('Difference (deg)')

    plt.tight_layout()
    plt.savefig('boxPlotTest_7.3.png')

    return differences_test1, differences_test2, differences_test3

def print_metrics(abs_diff):
    max_diff = np.max(abs_diff)
    mean_diff = np.mean(abs_diff)

    print(f"Max Difference: {max_diff}")
    print(f"Mean Difference: {mean_diff}")

    # Calculate IQR
    q1 = np.percentile(abs_diff, 25)  # 25th percentile
    q3 = np.percentile(abs_diff, 75)  # 75th percentile
    iqr = q3 - q1

    print(f"IQR: {iqr}")

    # Calculate Confidence Interval using t-distribution
    # standard deviation
    std_dev = np.std(abs_diff, ddof=1)  # Sample standard deviation
    n = len(abs_diff)  # Sample size

    # Confidence level (95%)
    confidence_level = 0.95
    alpha = 1 - confidence_level
    t_critical = stats.t.ppf(1 - alpha / 2, df=n-1)  # t-critical value

    # Margin of Error
    margin_of_error = t_critical * (std_dev / np.sqrt(n))

    # Confidence Interval
    ci_lower = mean_diff - margin_of_error
    ci_upper = mean_diff + margin_of_error

    print(f"Confidence Interval (95%): [{ci_lower}, {ci_upper}]")
    print(f"Margin of Error: {margin_of_error}")

# Main execution
def main():
    target_steps1, target_steps3, steps_test1, steps_test2, steps_test3 = get_data()
    differences_test1, differences_test2, differences_test3 = analyze_and_plot(target_steps1, target_steps3, steps_test1, steps_test2, steps_test3)

    # Absolute Differences
    abs_diff_test1 = np.abs(differences_test1)
    abs_diff_test2 = np.abs(differences_test2)
    abs_diff_test3 = np.abs(differences_test3)

    # Print Metrics
    print("Test 7.1 and 7.2:")
    print_metrics(np.concatenate((abs_diff_test1, abs_diff_test2)))
    print("Test 7.3:")
    print_metrics(abs_diff_test3)

    print("Values for the tests")
    print("Target for test 7.1 and 7.2")
    print(np.round(steps_to_degrees(target_steps1), 2))
    print("Test 7.1")
    print(np.round(steps_to_degrees(steps_test1), 2))
    print("Test 7.1 Error")
    print(np.round(differences_test1 ,2))
    print("Test 7.2")
    print(np.round(steps_to_degrees(steps_test2), 2))
    print("Test 7.2 Error")
    print(np.round(differences_test2 ,2))
    print("Target for test 7.3")
    print(np.round(steps_to_degrees(target_steps3), 2))
    print("Test 7.3")
    print(np.round(steps_to_degrees(steps_test3), 2))
    print("Test 7.3 Error")
    print(np.round(differences_test3 ,2))
    



if __name__ == "__main__":
    main()