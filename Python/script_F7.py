#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 25 12:20:11 2025
Script that compares the difference in injection-seismicty response between Oracle and ETAS fits.
Used to make Figure 7.
"""

# Import relevant libraries.
import torch
import numpy as np
import matplotlib.pyplot as plt
from torch.distributions import Categorical

import eq
from eq.data import SequenceIS
from eq.catalogs import IScases
from eq.data.batch import BatchIS
import eq.distributions as dist

# Pick the case for plotting.
partition_list = ['Basel','SSFS','CB','St1','FORGE','PNR1','PNR2']
test_case = 'Basel'
test_partition = 'Basel'
val_partition = 'PNR2'
f = 0.50

# Get the save path for models.
oracle_model_savepath = 'models/Vanilla/Model_' + test_partition + '_' + val_partition + '.pt'
etas_model_savepath = 'models/ETAS/Model_' + test_case + '_etas.pt'

# Get the corresponding Oracle model.
model_O = eq.models.Oracle()
model_O.load_state_dict(torch.load(oracle_model_savepath))
model_O.eval()

# Get some data for examining the Oracle-predicted EQ-inj response.
d = next(iter(IScases(test_case).dataset.get_dataloaderIS()))
seq =  d.get_sequence(0)
m = model_O.get_marks(d)
p = model_O.get_pre_params(m)
dT = model_O.get_dT_dist(p)
dTmean = dT.mean[0]

# Get some data for examining the ETAS-predicted EQ-inj response.
model_E = eq.models.ETAS_IS()
model_E.load_state_dict(torch.load(etas_model_savepath))
model_E.eval()

# Prep a synthetic dataset.
v = np.log10(np.arange(0,15,0.1))
dV = np.diff(v, prepend=0)
T = np.ones_like(v,shape=len(v)+1)
ones=np.ones_like(v)
seq_syn = SequenceIS(
    inter_times=torch.as_tensor(T, dtype=torch.float32),
    t_start=0,
    t_end=T.sum(),
    mag=torch.as_tensor(seq.mag.mean()*ones, dtype=torch.float32),
    vm=torch.as_tensor(v, dtype=torch.float32),
    dVc=torch.as_tensor(dV, dtype=torch.float32),
    sv=torch.as_tensor(ones, dtype=torch.float32),
    dTS=torch.as_tensor(-10*ones, dtype=torch.float32),
    Vc=torch.as_tensor(ones, dtype=torch.float32),
    Mo=torch.as_tensor(ones, dtype=torch.float32),
    Pm=torch.as_tensor(ones, dtype=torch.float32),
    pm=torch.as_tensor(ones, dtype=torch.float32),
    dP=torch.as_tensor(ones, dtype=torch.float32),
    sp=torch.as_tensor(ones, dtype=torch.float32),
    Eh=torch.as_tensor(ones, dtype=torch.float32),
    dEh=torch.as_tensor(ones, dtype=torch.float32),
    aRs=torch.as_tensor(ones, dtype=torch.float32),
    inj_time=torch.as_tensor(ones, dtype=torch.float32),
    inj_rate=torch.as_tensor(v, dtype=torch.float32),
    inj_dvol=torch.as_tensor(dV, dtype=torch.float32),
    inj_sign=torch.as_tensor(ones, dtype=torch.float32),
    inj_tsgn=torch.as_tensor(-10*ones, dtype=torch.float32),
    mag_completeness=seq.mag_completeness,
)
batch_syn = BatchIS.from_list([seq_syn])

# Get Oracle's response to the hypothetical injections.
cf = model_O.get_context(h[:,[round(f*h.shape[1])],:],batch_syn, forecasting=True,use_injection=True).squeeze(0)
dTf = model_O.get_inter_time_dist(cf)
dTmeanf = dTf.mean[0]
RfO = dTf.log_hazard(dTmeanf).T.reshape(-1).exp().log10()

# Get the ETAS response to the hypothetical injections.
RfE = model_E.evaluate_intensity(seq_syn)[1].log10()

# Make into numpy arrays.
RfO = RfO.detach().numpy()
RfE = RfE.detach().numpy()



## Plotting.

# Plotting colors.
colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

# Plot the sequence.
fig, ax = plt.subplots()
fig.set_size_inches(5.0, 4.5)
ax.plot(v,RfO, color='red', marker='o', linestyle='-')
ax.plot(v,RfE, color='black', linestyle='-')
ax.set_ylabel('Seismicity Rate (-log$_{10}$[min])')
ax.set_xlabel('Injection Rate (log$_{10}$[m$^3$/min])')
plt.savefig('F7.eps', format='eps')
plt.show()






