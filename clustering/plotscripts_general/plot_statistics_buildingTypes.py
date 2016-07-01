__author__ = 'Annika Wierichs'

import matplotlib.pyplot as plt
import matplotlib as mpl
import os

mpl.rcParams['font.size'] = 16.0

# The slices will be ordered and plotted counter-clockwise.
labels = '1 Apartment', '2 Apartments', '3-6 Apartments', '7-12 Apartments', '> 12 Apartments'
sizes = [65.1, 17.2, 11.8, 4.7, 1.2]
colors = ['yellowgreen', 'darkorange', 'gold', 'lightskyblue', 'lightcoral']

plt.figure(facecolor='white')
patches, texts = plt.pie(sizes, colors=colors, startangle=90)
plt.legend(patches, labels, loc="lower left")

# Set aspect ratio to be equal so that pie is drawn as a circle.
plt.axis('equal')

plt.show()
