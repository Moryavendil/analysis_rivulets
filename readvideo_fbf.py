import os
import cv2
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

plt.rcParams["figure.figsize"] = (12, 8)

from matplotlib.colors import Normalize # colormaps

from tools import datareading
#%%
# Dataset selection
dataset = '20241104'
dataset_path = '../' + dataset
print('Available acquisitions:', datareading.find_available_videos(dataset_path))
#%%
# Acquisition selection
acquisition = '100seuil_gcv'
acquisition_path = os.path.join(dataset_path, acquisition)
datareading.is_this_a_video(acquisition_path)
#%%
# see the frame
relative_colorscale:bool = False
remove_median_bckgnd = True #remove the mediab img, practical for dirt on plate
median_correc = False # remove the median value over each z line. helps with the heterogenous lighting.
remove_bright_spots = False # removes bright spots by accepting cmap saturation (1%)

normalize_each_image = False
#%%
# Parameters definition
framenumbers = np.arange(datareading.get_number_of_available_frames(acquisition_path))
roi = None, None, None, None  #start_x, start_y, end_x, end_y
if acquisition=='drainagelent':
    roi = 800, 600, 1400, 900  #start_x, start_y, end_x, end_y
#%%
# Data fetching
frames = datareading.get_frames(acquisition_path, framenumbers = framenumbers, subregion=roi)
length, height, width = frames.shape

acquisition_frequency = datareading.get_acquisition_frequency(acquisition_path, unit="Hz")
t = datareading.get_times(acquisition_path, framenumbers=framenumbers, unit='s')

print(f'Dataset: "{dataset}", acquisition: "{acquisition}"')
print(f'Frames dimension: {height}x{width}')
print(f'Length: {length} frames ({round(datareading.get_acquisition_duration(acquisition_path, framenumbers=framenumbers, unit="s"), 2)} s)')
print(f'Acquisition frequency: {round(datareading.get_acquisition_frequency(acquisition_path, unit="Hz"), 2)} Hz')
if (not(datareading.are_there_missing_frames(acquisition_path))):
    print(f'No dropped frames :)')
else:
    print(f'Dropped frames...')
#%%
# luminosity corrections
if remove_median_bckgnd:
    median_bckgnd = np.median(frames, axis=0, keepdims=True)
    frames = frames - median_bckgnd

if median_correc:
    frames = frames - np.median(frames, axis=(0,1), keepdims=True)

# if remove_median_bckgnd or median_correc:
#     frames -= frames.min()
#     frames *= 255/frames.max()

if normalize_each_image:
    # frames.setflags(write=1)
    # im = np.zeros_like(frames[0])
    # for i in range(length):
    #     cv2.normalize(frames[i], im, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
    #     frames[i] = im
    frames = frames - frames.min(axis = (1,2), keepdims=True)
    # frames *= 255/frames.max(axis=0, keepdims=True)

vmin_absolutecmap = frames.min()
vmax_absolutecmap = frames.max()
if remove_bright_spots:
    vmin_absolutecmap = np.percentile(frames.flatten(), 1)
    vmax_absolutecmap = np.percentile(frames.flatten(), 99)
#%%
def on_press(event):
    # print('press', event.key)
    global height, width
    # Navigation
    global i
    if event.key == 'right':
        i += 1
    if event.key == 'left':
        i -= 1
    if event.key == 'shift+right':
        i += 10
    if event.key == 'shift+left':
        i -= 10
    if event.key == 'up':
        i += 100
    if event.key == 'down':
        i -= 100

    update_display()

def update_display():
    global i, fig
    global frames, t, length
    i = i % length
    s = t[i]%60
    m = t[i]//60
    ax.set_title(f't = {f"{m} m " if np.max(t[-1])//60 > 0 else ""}{s:.2f} s - frame {framenumbers[i]} ({i+1}/{length})')

    frame = frames[i]

    global see_image, median_correc, remove_bright_spots
    global img
    if see_image:
        image = frame.astype(float)
        img.set_array(image)
        if relative_colorscale:
            vmin_relativecmap = image.min()
            vmax_relativecmap = image.max()
            if remove_bright_spots:
                vmin_relativecmap = np.percentile(image.flatten(), 1)
                vmax_relativecmap = np.percentile(image.flatten(), 99)
            relative_norm = Normalize(vmin=vmin_relativecmap, vmax=vmax_relativecmap)
            img.set_norm(relative_norm)

    fig.canvas.draw()
#%%
### Display
fig, ax = plt.subplots(1, 1)  # initialise la figure
fig.suptitle(f'{acquisition} ({dataset})')
ax.set_xlim(0, width)
ax.set_ylim(0, height)
plt.tight_layout()

see_image:bool = True
i = 0 # time

### ANIMATED ELEMENTS

# frame
img = ax.imshow(np.zeros((height, width)), origin='lower', vmin = vmin_absolutecmap, vmax = vmax_absolutecmap
                # , aspect='auto'
                )
if not see_image:
    img.set_cmap('binary') # white background

# initialize
update_display()

# plt.colorbar()

fig.canvas.mpl_connect('key_press_event', on_press)

plt.show()