#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 13:39:20 2025
Script to train OracleLite.
Largely used to test the performance of various encoder/decoder architectures.
"""

## Import relevant libraries.
import torch
import numpy as np
import matplotlib.pyplot as plt
import pytorch_lightning as pl
import pytorch_lightning.callbacks as pl_callbacks

import eq
from data_utils import get_Datasets



# Define training/validation/testing splits.
train_list = ['SSFS93','SSFS00','SSFS04','CB1a','CB1b','Basel']
val_list = ['SSFS05']
test_list = ['Basel']

# Get the dataloaders for the training/validation/test datasets.
(dl_train, Ne) = get_Datasets(train_list)
dl_val = get_Datasets(val_list)[0]
dl_test = get_Datasets(test_list)[0]
print('Number of events for training', Ne)

# Flag the types of supplementary marks considered.
M_marks = ['Mo','Vc']
P_marks = ['Pm','pm','dP','sp']
E_marks = ['Eh','dEh']
#supp_mark_list = [] + M_marks + P_marks + E_marks
supp_mark_list = []
supp_mark_tag = ''.join(supp_mark_list)

# Setup details for saving/logging.
model_savepath = 'modelExp.pt'
log_dir = 'logsExp'
chkpt_dir = 'checkpointsExp/'

#'''
# Define the model.
model = eq.models.OracleLite(supplementary_mark_list=supp_mark_list)

# Change early stopping loss metric, depending on forecasting type.
if model.train_to_forecast:
    loss_stop_type = 'val_forecast_loss'
else:
    loss_stop_type = 'val_fit_loss'

# Prep training modules.
early_stopping = pl_callbacks.EarlyStopping(monitor=loss_stop_type, patience=30, min_delta=1e-3)
checkpoint = pl_callbacks.ModelCheckpoint(dirpath=chkpt_dir, monitor=loss_stop_type, save_top_k=20)
tb_logger = pl.loggers.TensorBoardLogger(save_dir=log_dir)
num_gpus = int(torch.cuda.is_available())

# Trainer setup.
trainer = pl.Trainer( 
    max_epochs=100, 
    callbacks=[checkpoint, early_stopping], 
    #gradient_clip_val=5.0, gradient_clip_algorithm='norm', 
    logger=[tb_logger],
    #profiler='pytorch',
    )

# Train the model, and then select the best one via validation loss.
trainer.fit(model, dl_train, dl_val)
best_model_list = sorted(checkpoint.best_k_models, key=checkpoint.best_k_models.get)
model = eq.models.OracleLite.load_from_checkpoint(best_model_list[0])
torch.save(model.state_dict(), model_savepath)

# Test evaluation.
trainer.test(model, dl_test)
#'''


#'''
## Plotting.
model = eq.models.OracleLite(supplementary_mark_list=supp_mark_list)
model.load_state_dict(torch.load(model_savepath))
model.eval()

# Get some data for plotting.
d = next(iter(dl_test))
seq =  d.get_sequence(0)
m = model.get_marks(d)
dT = model.get_dT(m)

# Validation loss.
print('Test loss')
print(model.loss(d))
print('Validation loss')
print(model.loss(next(iter(dl_val))))

# Get the mean rates from fitting.
Rm = dT.squeeze(0).detach().numpy()
Rm = -np.log10((Rm))[0:-1]

# Get the mean rates from forecasting.
if model.train_to_forecast:
    idx = round(0.15*d.inter_times.shape[1])
else:
    idx = 0
dTf = model.get_dT(m,forecasting=model.train_to_forecast,idx_split=idx)
Rmf = dTf.squeeze(0).detach().numpy()
Rmf = -np.log10((Rmf))[0:-1]

# Prep the input data for plotting.
te = seq.arrival_times.numpy()
Re = -np.log10(seq.inter_times.numpy()[0:-1])
ti = seq.inj_time.numpy()
Ir=seq.inj_rate.numpy()
aRs = seq.aRs.numpy()

# Plot.
plt.plot(te,Re, color='red', marker='o', linestyle='')
plt.plot(ti,Ir, color='blue', linestyle = '-')
plt.plot(te,Rm, color='pink', marker='+', linestyle='')
plt.plot(te,aRs, color='maroon', marker='', linestyle='-')
plt.plot(te[0:idx],Rm[0:idx], color='gray', marker='', linestyle='--')
plt.plot(te[  idx],Rm[  idx], color='gray', marker='o', linestyle='')
plt.plot(te[idx: ],Rmf,       color='gray', marker='', linestyle='-')
#plt.ylim(-4,2.5)
#plt.xlim(2500,8500)
#'''


