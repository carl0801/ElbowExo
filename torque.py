import numpy as np
import matplotlib.pyplot as plt

def draw_elbow(inner_radius, outer_radius, angle, lower_arm_length):
    fig, ax = plt.subplots(subplot_kw={'aspect': 'equal'})
    
    # Create the inner arc
    theta = np.linspace(np.pi, np.pi + np.radians(angle), 100)
    x_inner = inner_radius * np.cos(theta)
    y_inner = inner_radius * np.sin(theta)
    ax.plot(x_inner, y_inner, 'b--', label='Inner Arc')
    
    # Create the outer arc
    x_outer = outer_radius * np.cos(theta)
    y_outer = outer_radius * np.sin(theta)
    ax.plot(x_outer, y_outer, 'r-', label='Outer Arc')
    
    # Create the lines connecting the arcs
    ax.plot([x_inner[0], x_outer[0]], [y_inner[0], y_outer[0]], 'k-')
    ax.plot([x_inner[-1], x_outer[-1]], [y_inner[-1], y_outer[-1]], 'k-')
    
    # Calculate the end points of the lower arm rectangle
    end_x1 = x_outer[-1] + lower_arm_length * np.cos(np.pi + np.radians(angle))
    end_y1 = y_outer[-1] + lower_arm_length * np.sin(np.pi + np.radians(angle))
    
    end_x2 = x_inner[-1] + lower_arm_length * np.cos(np.pi + np.radians(angle))
    end_y2 = y_inner[-1] + lower_arm_length * np.sin(np.pi + np.radians(angle))
    
# Draw a line from (0, -5) to (0, -10)
    ax.plot([0, 0], [-5, -10], 'g-', label='Lower Arm')
    #
    ax.plot([lower_arm_length, lower_arm_length], [-5, -10], 'g-', label='Lower Arm')
    ax.plot([0, lower_arm_length], [-10, -10], 'g-', label='Lower Arm')
    ax.plot([0, lower_arm_length], [-5, -5], 'g-', label='Lower Arm')
    
    plt.title('Elbow Diagram with Lower Arm')
    plt.legend()
    plt.show()



def calculate_torque(kg, distance, angle):
    force = kg * 9.81
    angle = np.radians(angle)
    return force * distance*np.sin(angle)


#15.7 % of total height 171.45 cm
percentage_of_total_height = 15.7 # lowerarm Percentage of total height
average_height = 188.7 # cm
hand = 5.75/100 * average_height
print(hand)
print(percentage_of_total_height/100 * average_height)
print(percentage_of_total_height/100 * average_height + hand)
distance = percentage_of_total_height/100 * average_height*0.01
print(distance)
# 140 kg mand 158 g tallerken 400 g mad
kg = 2.6 + 0.8+ 0.423
# Example usage
#draw_elbow(inner_radius=5, outer_radius=10, angle=90, lower_arm_length=distance*100)
torque = calculate_torque(kg, distance, angle=90)
print('Torque: %.2f Nm' % torque)
print((0.800 + 0.423 + 2.6) * 9.82 * 0.296 * np.sin(np.radians(90)))