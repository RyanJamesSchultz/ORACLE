#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 10:48:55 2025
Script used to prototype the training process, tune hyper-parameters, etc.
"""

## Import relevant libraries.
import torch
import numpy as np
import matplotlib.pyplot as plt
import pytorch_lightning as pl
import pytorch_lightning.callbacks as pl_callbacks

import eq
from eq.catalogs import IScases
from data_utils import get_Datasets
#from eq.models.oracle_old import Oracle



# Define training/validation/testing splits.
train_list = ['SSFS93','SSFS00','SSFS04','CB1a','CB1b','Basel']
val_list = ['SSFS05']
test_list = ['Basel']

# Get the dataloaders for the training/validation/test datasets.
(dl_train, Ne) = get_Datasets(train_list)
dl_val = get_Datasets(val_list)[0]
dl_test = get_Datasets(test_list)[0]
print('Number of events for training',Ne)

# Flag the types of supplementary marks considered.
M_marks = ['Mo','Vc']
P_marks = ['Pm','pm','dP','sp']
E_marks = ['Eh','dEh']
supp_mark_list = []
#supp_mark_list = []+M_marks+P_marks+E_marks

# Setup details for saving/logging.
model_savepath = 'modelExp.pt'
log_dir = 'logsExp'
chkpt_dir = 'checkpointsExp/'

#'''
# Define the model.
model = eq.models.Oracle(supplementary_mark_list=supp_mark_list)

# Change early stopping loss metric, depending on forecasting type.
if model.train_to_forecast:
    loss_stop_type = 'val_forecast_loss'
else:
    loss_stop_type = 'val_fit_loss'

# Prep training modules.
early_stopping = pl_callbacks.EarlyStopping(monitor=loss_stop_type, patience=30, min_delta=1e-4)
checkpoint = pl_callbacks.ModelCheckpoint(dirpath=chkpt_dir, monitor=loss_stop_type, save_top_k=20)
tb_logger = pl.loggers.TensorBoardLogger(save_dir=log_dir)
num_gpus = int(torch.cuda.is_available())

# Trainer setup.
trainer = pl.Trainer( 
    max_epochs=100, 
    callbacks=[checkpoint, early_stopping], 
    #gradient_clip_val=1.0, gradient_clip_algorithm='norm', 
    logger=[tb_logger], 
    #profiler='pytorch', 
    )

# Train the model, and then select the best one via validation loss.
trainer.fit(model, dl_train, dl_val)
best_model_list = sorted(checkpoint.best_k_models, key=checkpoint.best_k_models.get)
model = eq.models.Oracle.load_from_checkpoint(best_model_list[0])
torch.save(model.state_dict(), model_savepath)

# Test evaluation.
trainer.test(model, dl_test)
#'''


#'''
## Plotting.
model = eq.models.Oracle(supplementary_mark_list=supp_mark_list)
model.load_state_dict(torch.load(model_savepath))
model.eval()

# Get some data for plotting.
cat = IScases(test_list[0])
d = next(iter(cat.dataset.get_dataloaderIS()))
m = model.get_marks(d)
p = model.get_pre_params(m)
dT = model.get_dT_dist(p)

# Get the mean rates from fitting.
Rm = dT.mean.squeeze(0).detach().numpy()
Rm = -np.log10((Rm[0:-1]))

# Get the intensity values from fitting.
tr,Rf = model.evaluate_intensity(sequence=cat.full_sequence,num_grid_points=0)
tr = tr.numpy()
Rf = Rf.log10().detach().numpy()

# Get some compensator values from fitting.
tc,Cf = model.evaluate_compensator(sequence=cat.full_sequence,num_grid_points=0)
tc = tc.numpy()
Cf = Cf.detach().numpy()

# Get the nLL values from fitting.
Lf = model.evaluate_nll(cat.full_sequence)
Lf = Lf.detach().numpy()

# Prep the input data for plotting.
te = cat.full_sequence.arrival_times.numpy()
Re = -np.log10(cat.full_sequence.inter_times.numpy()[0:-1])
ti = cat.full_sequence.inj_time.numpy()
Ir=cat.full_sequence.inj_rate.numpy()

# Get the intensity from forecast estimation.
t_forecast = cat.full_sequence.t_start+0.22*(cat.full_sequence.t_end-cat.full_sequence.t_start)
tf1,tf2,If1,If2,Rmf = model.forecast_intensity(sequence=cat.full_sequence,t_forecast=t_forecast)
#tr,Rf = model.evaluate_intensity(sequence=cat.full_sequence,num_grid_points=0)
tf1 = tf1.numpy()
tf2 = tf2.numpy()
If1 = If1.log10().detach().numpy()
If2 = If2.log10().detach().numpy()
Rmf = Rmf.detach().numpy()
Rmf = -np.log10(Rmf)

# Get the mean rates from forecasting.

# Plot.
plt.plot(te,Re, color='red', marker='o', linestyle='')
plt.plot(tr,Rf, color='black', linestyle='-')
plt.plot(ti,Ir, color='blue', linestyle = '-')
plt.plot(te,Rm, color='pink', marker='+', linestyle='')
plt.plot(tf2,Rmf, color='lavenderblush', marker='.', linestyle='')
plt.plot(tf1,If1, color='silver', linestyle=':')
plt.plot(tf2,If2, color='grey', linestyle='-')
#plt.plot(tr,Lf, color='green', linestyle='--')
#plt.plot(tc,Cf, color='green', linestyle='-')
plt.ylim(-4,2.5)
#plt.xlim(2500,8500)
#'''

