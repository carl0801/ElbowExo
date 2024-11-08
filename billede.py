import cv2
import numpy as np
import matplotlib.pyplot as plt

# load image
path = "C:\\Users\\emilr\\OneDrive\\Desktop\\expectations.png"

img = cv2.imread(path)

# show in matplotlib
plt.imshow(img)
plt.show()

#204,203,202

#loop through image and find all pixels with the color 204,203,202 and change them to 255,255,255
for i in range(img.shape[0]):
    for j in range(img.shape[1]):
        if img[i,j][0] == 204 and img[i,j][1] == 203 and img[i,j][2] == 202:
            img[i,j] = [255,255,255]

# show in matplotlib
plt.imshow(img)
plt.show()

# save image
cv2.imwrite("C:\\Users\\emilr\\OneDrive\\Desktop\\expectations.png", img)