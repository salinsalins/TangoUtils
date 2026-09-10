import math

import matplotlib.pyplot as plt
import numpy as np

from matplotlib import cm
from matplotlib.ticker import LinearLocator

fig, ax = plt.subplots(subplot_kw={"projection": "3d"})

# Make data.
X = np.arange(0, np.pi, np.pi*0.01)
Y = np.arange(0, np.pi, np.pi*0.01)
X, Y = np.meshgrid(X, Y)
# R = np.sqrt(X**2 + Y**2)
Z = np.sin(X)**2 - np.sin(Y)**2 - np.sin(X+Y)**2

Z = Z * (Z > 0.0)
Z = Z * ((X+Y) < 1.0*np.pi)

# Plot the surface.
surf = ax.plot_surface(X, Y, Z, cmap=cm.coolwarm,
                       linewidth=0, antialiased=False)

# Customize the z axis.
ax.set_zlim(0., .25)
ax.zaxis.set_major_locator(LinearLocator(10))
# A StrMethodFormatter is used automatically
ax.zaxis.set_major_formatter('{x:.02f}')

# Add a color bar which maps values to colors.
fig.colorbar(surf, shrink=0.5, aspect=5)

plt.show()

fig, ax = plt.subplots()
im = ax.imshow(Z, interpolation='bilinear', origin='lower',
               cmap=cm.coolwarm, extent=(0., 360., 0., 360.))
levels = np.arange(0, Z.max(), Z.max()/5.)
CS = ax.contour(Z, levels, origin='lower', cmap='flag', extend='both',
                linewidths=2, extent=(0., 360., 0., 360.))
#
# # Thicken the zero contour.
# lws = np.resize(CS.get_linewidth(), len(levels))
# lws[6] = 4
# CS.set_linewidth(lws)
#
# ax.clabel(CS, levels[1::2],  # label every second level
#           inline=True, fmt='%1.1f', fontsize=14)
#
# # make a colorbar for the contour lines
# CB = fig.colorbar(CS, shrink=0.8)
#
# ax.set_title('Lines with colorbar')
#
# # We can still add a colorbar for the image, too.
# CBI = fig.colorbar(im, orientation='horizontal', shrink=0.8)
#
# # This makes the original colorbar look a bit out of place,
# # so let's improve its position.
#
# l, b, w, h = ax.get_position().bounds
# ll, bb, ww, hh = CB.ax.get_position().bounds
# CB.ax.set_position([ll, b + 0.1*h, ww, h*0.8])

plt.show()
