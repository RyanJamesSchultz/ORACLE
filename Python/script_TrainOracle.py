#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 15 13:39:20 2025
Script to train all the Oracle models using k-fold cross validation.
"""

## Import relevant libraries.
import torch
import numpy as np
import matplotlib.pyplot as plt
import pytorch_lightning as pl
import pytorch_lightning.callbacks as pl_callbacks

import eq
from data_utils import get_kFold_datasets_test

import argparse



# Get test case from the (optional) input arguments.
parser = argparse.ArgumentParser()
parser.add_argument('--test',type=str)
args = parser.parse_args()
if args.test:
    test_list = [args.test]
else:
    test_list = ['Basel']

# Loop over all of the test partitions.
for case_test in test_list:

    # Loop over all of the k-fold validation partitions.
    val_list = ['Basel','SSFS','CB','St1','FORGE','PNR1','PNR2']
    val_list.remove(case_test)
    #val_list = ['CB']
    for case_val in val_list:

        # Get the dataloaders for the training/validation/test datasets.
        (dl_train,dl_val,dl_test, Nt,Nv,Ne) = get_kFold_datasets_test(case_test,case_val)
        print('Number of events for training', Nt)
        print('Test: ', case_test)
        print('Val:  ', case_val)
        #dl_train.num_workers=2

        # Flag the types of supplementary marks considered.
        M_marks = ['Mo', 'Vc']
        P_marks = ['Pm','pm','dP','sp']
        E_marks = ['Eh','dEh']
        supp_mark_list = []
        #supp_mark_list = []+M_marks+P_marks+E_marks
        
        # Get a string to differentiate model variants based on supplementary mark use.
        if not supp_mark_list:
            supp_mark_tag = 'Vanilla'
        else:
            supp_mark_tag = ''.join(supp_mark_list)

        # Setup details for saving/logging.
        model_savepath = 'models/' + supp_mark_tag + '/Model_' + case_test + '_' + case_val + '.pt'
        log_dir = 'logs/' + supp_mark_tag + '/'
        chkpt_dir = log_dir + case_test + '/' + case_val + '/checkpoints/'

        #'''
        # Define the model.
        model = eq.models.Oracle(supplementary_mark_list=supp_mark_list)
        
        # Change early stopping loss metric, depending on forecasting type.
        if model.train_to_forecast:
            loss_stop_type = 'val_forecast_loss'
        else:
            loss_stop_type = 'val_fit_loss'

        # Prep training modules.
        early_stopping = pl_callbacks.EarlyStopping(monitor=loss_stop_type, patience=100, min_delta=1e-4)
        checkpoint = pl_callbacks.ModelCheckpoint(dirpath=chkpt_dir, monitor=loss_stop_type, save_top_k=20)
        tb_logger = pl.loggers.TensorBoardLogger(save_dir=log_dir, name=case_test, version=case_val)
        num_gpus = int(torch.cuda.is_available())

        # Trainer setup.
        trainer = pl.Trainer( 
            max_epochs=1500, 
            callbacks=[checkpoint, early_stopping], 
            #gradient_clip_val=3.0, gradient_clip_algorithm='norm', 
            logger=[tb_logger],
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
d = next(iter(dl_test))
seq =  d.get_sequence(0)
m = model.get_marks(d)
p = model.get_pre_params(m)
dT = model.get_dT_dist(p)

# Validation loss.
print('Test loss')
print(model.loss(d))
print('Validation loss')
print(model.loss(next(iter(dl_val))))

# Get the mean rates from fitting.
Rm = dT.mean.squeeze(0).detach().numpy()
Rm = -np.log10((Rm[0:-1]))

# Get the intensity values from fitting.
tr,Rf = model.evaluate_intensity(sequence=seq,num_grid_points=0)
tr = tr.numpy()
Rf = Rf.log10().detach().numpy()

# Get some compensator values from fitting.
tc,Cf = model.evaluate_compensator(sequence=seq,num_grid_points=0)
tc = tc.numpy()
Cf = Cf.detach().numpy()

# Get the nLL values from fitting.
Lf = model.evaluate_nll(seq)
Lf = Lf.detach().numpy()

# Prep the input data for plotting.
te = seq.arrival_times.numpy()
Re = -np.log10(seq.inter_times.numpy()[0:-1])
ti = seq.inj_time.numpy()
Ir=seq.inj_rate.numpy()

# Get the intensity from forecast estimation.
t_forecast = seq.t_start+0.12*(seq.t_end-seq.t_start)
tf1,tf2,If1,If2,Rmf = model.forecast_intensity(sequence=seq,t_forecast=t_forecast)
#tr,Rf = model.evaluate_intensity(sequence=seq,num_grid_points=0)
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
