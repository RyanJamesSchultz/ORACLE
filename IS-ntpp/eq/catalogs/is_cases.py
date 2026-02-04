import io
from pathlib import Path
from typing import Tuple, Union

import numpy as np
import pandas as pd
import requests
import torch

from eq.data import Catalog, InMemoryDataset, SequenceIS, default_catalogs_dir


class IScases(Catalog):

    def __init__(
        self,
        CaseID,
        #mag_completeness: float = -1.5,
        #train_start_ts: pd.Timestamp = pd.Timestamp("2009-01-01"),
        #val_start_ts: pd.Timestamp = pd.Timestamp("2014-01-01"),
        #test_start_ts: pd.Timestamp = pd.Timestamp("2017-01-01"),
    ):
        root_dir = default_catalogs_dir / CaseID
        metadata=torch.load(root_dir / 'metadata.pt', weights_only=False)
        super().__init__(root_dir=root_dir, metadata=metadata)

        self.full_sequence = InMemoryDataset.load_from_disk(
            self.root_dir / 'full_sequence.pt'
        )[0]
        
        self.dataset=InMemoryDataset([self.full_sequence])

        #self.metadata["train_start_ts"] = pd.Timestamp(train_start_ts)
        #self.metadata["val_start_ts"] = pd.Timestamp(val_start_ts)
        #self.metadata["test_start_ts"] = pd.Timestamp(test_start_ts)
        #seq_train, seq_val, seq_test = train_val_test_split_sequence(
        #    seq=self.full_sequence,
        #    start_ts=self.metadata["start_ts"],
        #    train_start_ts=self.metadata["train_start_ts"],
        #    val_start_ts=self.metadata["val_start_ts"],
        #    test_start_ts=self.metadata["test_start_ts"],
        #)

        #self.train = InMemoryDataset([seq_train])
        #self.val = InMemoryDataset([seq_val])
        #self.test = InMemoryDataset([seq_test])

    @property
    def required_files(self):
        return ['full_sequence.pt', 'metadata.pt']

    def generate_catalog(CaseID):

        # Load in the csv files as dataframes.
        root_dir=default_catalogs_dir / CaseID
        f_hed=CaseID+'_Hed.csv'
        f_cat=CaseID+'_Cat.csv'
        f_inj=CaseID+'_Inj.csv'
        df_hed=pd.read_csv(root_dir / f_hed)
        df_cat=pd.read_csv(root_dir / f_cat)
        df_inj=pd.read_csv(root_dir / f_inj)

        # Save full event sequence as InMemoryDataset
        #start_ts = self.metadata["start_ts"]
        #end_ts = self.metadata["end_ts"]

        # Get the header information.
        t_start = df_hed['Start Time (min)'].to_numpy()[0] # Minutes. # Minutes.
        t_end = df_hed['End Time (min)'].to_numpy()[0] # Minutes.
        mag_completeness = df_hed['Magnitude of Completeness (M)'].to_numpy()[0] # M.

        # Get the catalogue.
        arrival_times = df_cat['Time (min)'].to_numpy() # Minutes
        inter_times = df_cat['Inter-event Time (log10[min])'].to_numpy() # log10(Minutes)
        mag = df_cat['Magnitude (M)'].to_numpy()

        # Get the inter-event times.
        inter_times=np.power(10,inter_times)
        inter_times=np.append(inter_times, t_end-arrival_times[-1])

        # Get the supplementary marks.
        vm = df_cat['Instantaneous Injection Rate (log10[m3/min])'].to_numpy() # log10(m3/min)
        dVc = df_cat['Sequential Volume Change (log10[m3])'].to_numpy() # log10(m3)
        sv = df_cat['Sign of Sequential Volume Change (-)'].to_numpy() # -
        dTS = df_cat['Time Since Injection Sign Change (log10[min])'].to_numpy() # -
        Vc = df_cat['Cumulative Volume (log10[m3])'].to_numpy() # log10(m3)
        Mo = df_cat['Cumulative Moment (M)'].to_numpy() # M
        Pm = df_cat['Pressure (log10[MPa])'].to_numpy() # log10(MPa)
        pm = df_cat['Instantaneous Pressure Rate (log10[MPa/min])'].to_numpy() # log10(MPa/min)
        dP = df_cat['Sequential Pressure Change (log10[MPa])'].to_numpy() # log10(MPa)
        sp = df_cat['Sign of Pressure Change (-)'].to_numpy() # -
        Eh = df_cat['Cumulative Hydraulic Moment (M)'].to_numpy() # M
        dEh = df_cat['Sequential Hydraulic Moment Change (M)'].to_numpy() # M
        aRs = df_cat['Smoothed Causal Seismicity Rate log10[1/min]'].to_numpy() # log10(1/min)

        # Get the injection information.
        inj_time=df_inj['Time (min)'].to_numpy() # Minutes
        inj_rate=df_inj['Injection Rate (log10[m3/min])'].to_numpy() # log10(m3/min)
        inj_dvol=df_inj['Sequential Volume Change (log10[m3])'].to_numpy() # log10(m3)
        inj_sign=df_inj['Sign of Injection Rate (-)'].to_numpy() # -
        inj_tsgn=df_inj['Time Since Injection Sign Change (log10[min])'].to_numpy() # -

        # Check for errors.
        #assert subset_df.time.min() > start_ts
        #assert subset_df.time.max() < end_ts

        # Make the sequence object.
        seq_cat = SequenceIS(
            inter_times=torch.as_tensor(inter_times, dtype=torch.float32),
            t_start=t_start,
            t_end=t_end,
            mag=torch.as_tensor(mag, dtype=torch.float32),
            vm=torch.as_tensor(vm, dtype=torch.float32),
            dVc=torch.as_tensor(dVc, dtype=torch.float32),
            sv=torch.as_tensor(sv, dtype=torch.float32),
            dTS=torch.as_tensor(dTS, dtype=torch.float32),
            Vc=torch.as_tensor(Vc, dtype=torch.float32),
            Mo=torch.as_tensor(Mo, dtype=torch.float32),
            Pm=torch.as_tensor(Pm, dtype=torch.float32),
            pm=torch.as_tensor(pm, dtype=torch.float32),
            dP=torch.as_tensor(dP, dtype=torch.float32),
            sp=torch.as_tensor(sp, dtype=torch.float32),
            Eh=torch.as_tensor(Eh, dtype=torch.float32),
            dEh=torch.as_tensor(dEh, dtype=torch.float32),
            aRs=torch.as_tensor(aRs, dtype=torch.float32),
            inj_time=torch.as_tensor(inj_time, dtype=torch.float32),
            inj_rate=torch.as_tensor(inj_rate, dtype=torch.float32),
            inj_dvol=torch.as_tensor(inj_dvol, dtype=torch.float32),
            inj_sign=torch.as_tensor(inj_sign, dtype=torch.float32),
            inj_tsgn=torch.as_tensor(inj_tsgn, dtype=torch.float32),
            mag_completeness=mag_completeness,
        )

        # Save the sequences as InMemoryDatasets.
        dataset = InMemoryDataset(sequences=[seq_cat])
        dataset.save_to_disk(root_dir / 'full_sequence.pt')
        
        # Make and then save the metadata.
        metadata = {
            'name': CaseID,
            'freq': '1D',
            'mag_roundoff_error': 0.01,
            'mag_completeness"': mag_completeness,
            'start_ts': t_start,
            'end_ts': t_end,
        }
        torch.save(metadata, root_dir / 'metadata.pt')
