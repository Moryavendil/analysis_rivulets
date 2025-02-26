# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>
# <codecell>

# %matplotlib notebook

import os
import numpy as np
import matplotlib.pyplot as plt

from tools import set_verbose, datareading, datasaving, utility
utility.configure_mpl()


# <codecell>

### Datasets display
root_path = '../'
datasets = datareading.find_available_datasets(root_path)
print('Available datasets:', datareading.find_available_datasets(root_path))


# <codecell>

### Dataset selection & acquisitions display
dataset = '-'
if len(datasets) == 1:
    dataset = datasets[0]
    datareading.log_info(f'Auto-selected dataset {dataset}')
dataset_path = os.path.join(root_path, dataset)
datareading.describe_dataset(dataset_path, type='gcv', makeitshort=True)


# <codecell>

straight = ['20eta', '20seuil', '30eta', '30seuil', '40eta', '50eta', '70eta', '100eta', '200eta']
instab = ['20down', '30down', '30max', '40seuil', '40down', '40fix', '50seuil', '50mid', '50high', '70seuil', '70mid', '100seuil', '100mid', '200seuil', '200mid']


# <codecell>

### meta-info reading
import pandas as pd

workbookpath = os.path.join(dataset_path, 'datasheet.xlsx')

metainfo = pd.read_excel(workbookpath, sheet_name='metainfo', skiprows=2)

metakeys = [key for key in metainfo.keys() if 'unnamed' not in key.lower()]
metavalid = metainfo['acquisition_title'].astype(str) != 'nan'

m_acquisition_title = metainfo['acquisition_title'][metavalid].to_numpy()
m_n_pump       = metainfo['n_pump'][metavalid].to_numpy()
m_acquisition_frequency        = metainfo['acquisition_frequency'][metavalid].to_numpy()
m_exposure_time      = metainfo['exposure_time'][metavalid].to_numpy()
m_n_frames       = metainfo['n_frames'][metavalid].to_numpy()
m_excitation_frequency      = metainfo['excitation_frequency'][metavalid].to_numpy()
m_excitation_amplitude        = metainfo['excitation_amplitude'][metavalid].to_numpy()


# <codecell>


data_sheetname = 'autodata_3x4'

df_autodata = pd.read_excel(workbookpath, sheet_name=data_sheetname)
datakeys = [key for key in df_autodata.keys() if 'unnamed' not in key.lower()]

datavalid = df_autodata['(0,0)_freqt'].astype(str) != 'nan'
# datavalid = df_autodata['(0,1)_Z_amp'].astype(str) != 'nan'

N_acq = np.sum(datavalid)

acquisition_title = df_autodata['acquisition_title'][datavalid].to_numpy()

excitation_frequency = np.zeros(N_acq, dtype=float)
excitation_amplitude = np.zeros(N_acq, dtype=float)
for i in range(N_acq):
    excitation_amplitude[i] = float(m_excitation_amplitude[np.where(m_acquisition_title == acquisition_title[i])[0][0]])
    excitation_frequency[i] = float(m_excitation_frequency[np.where(m_acquisition_title == acquisition_title[i])[0][0]])


# <codecell>

n_k = np.arange(0, 2+1)
n_f = np.arange(-2, 1+1)

mode_if, mode_ik = np.meshgrid(n_f, n_k)

f = {}
q = {}
Z = {}
W = {}

for i_k, nk in enumerate(n_k):
    for i_f, nf in enumerate(n_f):
        modelabel = f'({mode_ik[i_k, i_f]},{mode_if[i_k, i_f]})'
        f[modelabel] = df_autodata[f'{modelabel}_freqt'][datavalid].to_numpy()
        q[modelabel] = df_autodata[f'{modelabel}_freqx'][datavalid].to_numpy()
        Z[modelabel] = df_autodata[f'{modelabel}_Z_amp'][datavalid].to_numpy()
        W[modelabel] = df_autodata[f'{modelabel}_W_amp'][datavalid].to_numpy()


F = excitation_frequency
Q = q['(1,0)']

V = -f['(1,0)'] / q['(1,0)']
C = -f['(1,-1)'] / q['(1,0)']


# <codecell>

N_acq


# <codecell>

# ### Check for bugs
# plt.figure()
# ax = plt.gca()
# ax.scatter(excitation_frequency, f['(0,1)'])
# ax.set_xlabel('f_ex')
# ax.set_ylabel('f_answer')


# <codecell>

plt.figure()
ax = plt.gca()

ax.scatter(F, Q)
for i in range(N_acq):
    ax.text(F[i], Q[i], str(excitation_amplitude[i]))
ax.set_xlabel('f')
ax.set_ylabel('q')


# <codecell>

plt.figure()
ax = plt.gca()

ax.scatter(F, V)
for i in range(N_acq):
    ax.text(F[i], -f['(1,0)'] , str(excitation_amplitude[i]))
ax.set_xlabel('f')
ax.set_ylabel('f_drift')


# <codecell>

plt.figure()
ax = plt.gca()

ax.scatter(F, V)
for i in range(N_acq):
    ax.text(F[i], V[i], str(excitation_amplitude[i]))
ax.set_xlabel('f')
ax.set_ylabel('v_drift')


# <codecell>

plt.figure()
ax = plt.gca()

ax.scatter(F, C)
for i in range(N_acq):
    ax.text(F[i], C[i], str(excitation_amplitude[i]))
ax.set_xlabel('f')
ax.set_ylabel('c')
ax.set_ylim(0, 350)


# <codecell>

plt.figure()
ax = plt.gca()

ax.scatter(F, W['(1,-1)'], label='Z')
ax.scatter(F, Z['(1,0)'], label='W')
for i in range(N_acq):
    ax.text(F[i], W['(1,-1)'][i], str(excitation_amplitude[i]))
for i in range(N_acq):
    ax.text(F[i], Z['(1,0)'][i], str(excitation_amplitude[i]))
ax.set_xlabel('f')
# ax.set_ylabel('c')
# ax.set_ylim(0, 350)


# <codecell>




# <codecell>



