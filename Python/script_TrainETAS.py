#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 16 10:48:55 2025
Script to fit the ETAS model on each of the IS sequences.
"""

## Import relevant libraries.
import pytorch_lightning as pl
import pytorch_lightning.callbacks as pl_callbacks
import torch
import eq
from eq.catalogs import IScases
import matplotlib.pyplot as plt
import numpy as np

# List of all the cases.
case_list = ['Basel', 
              'SSFS93','SSFS00','SSFS03','SSFS04','SSFS05', 
              'CB1a','CB1b','CB4', 'Paralana', 
              'St1-2018','St1-2020', 
              'FORGE-S1','FORGE-S2','FORGE-S3', 
              'PNR1z-a','PNR1z-b','PNR1z-c', 
              'PNR2-cWa','PNR2-cWb','PNR2-cE'
              ]
case_list = ['SSFS05']

# Loop over all of the test cases.
for case_test in case_list:

    # Define the model's name, for saving.
    model_savepath = 'models/ETAS/Model_' + case_test + '_etas.pt'
    log_dir = 'logs/ETAS/'
    chkpt_dir = log_dir + case_test + '/checkpoints/'

    ## Loading in the catalogue.
    catalog = IScases(case_test)

    #'''
    ## Define the validation and test datasets.
    dl_train = catalog.dataset.get_dataloaderIS()

    # Define the model.
    model = eq.models.ETAS_IS()

    # Training setup.
    early_stopping = pl_callbacks.EarlyStopping(monitor='val_fit_loss', patience=100, min_delta=1e-4)
    checkpoint = pl_callbacks.ModelCheckpoint(dirpath=chkpt_dir, monitor='val_fit_loss')
    tb_logger = pl.loggers.TensorBoardLogger(save_dir=log_dir, name=case_test, version='etas')
    num_gpus = int(torch.cuda.is_available())

    trainer = pl.Trainer(
        max_epochs=1500,
        callbacks=[checkpoint, early_stopping],
        logger=[tb_logger],
        )

    # Train the model, and find best model via validation.
    trainer.fit(model, dl_train, dl_train)
    model = eq.models.ETAS_IS.load_from_checkpoint(checkpoint.best_model_path)
    torch.save(model.state_dict(), model_savepath)

    ## Test evaluation.
    trainer.test(model, dl_train)
    print(model.loss(next(iter(dl_train))))

    # Report fitted ETAS parameters.
    print('\n')
    model.print_params()
    #'''



## Plotting.
model = eq.models.ETAS_IS()
model.load_state_dict(torch.load(model_savepath))
model.eval()

catalog = IScases(case_test)

# Get some intensity values.
tr,Rf=model.evaluate_intensity(sequence=catalog.full_sequence,num_grid_points=0)
tr=tr.numpy()
Rf=Rf.log10().detach().numpy()
#Rf=np.ones_like(Rf)
#tr=np.linspace(start=4000,stop=20000,num=Rf.shape[1])

# Some other vriables to plot.
te=catalog.full_sequence.arrival_times.numpy()
Re=np.log10(1/(catalog.full_sequence.inter_times.numpy()[0:-1]))
ti=catalog.full_sequence.inj_time.numpy()
Ir=catalog.full_sequence.inj_rate.numpy()

# Plot.
plt.plot(te,Re, color='red', marker='o', linestyle='')
plt.plot(tr,Rf, color='black', linestyle='-')
plt.plot(ti,Ir, color='blue', linestyle = '-')
