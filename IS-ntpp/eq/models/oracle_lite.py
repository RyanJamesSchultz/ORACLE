import random
from typing import List, Optional, Tuple, Union

import torch
import numpy as np

import eq
from eq.data.batch import BatchIS
from eq.data import SequenceIS
from .tpp_model import TPPModel



class OracleLite(TPPModel):
    """ Simplified version of Oracle, that only estimates the mean inter-event times.

    Args:
        input_magnitude: Should magnitude be used as a model input feature?
        input_injection: Should injection data be used as a model input feature?
        train_to_forecast: Should the model be trained to forecast the seqeunce too?
        supplementary_mark_list: List of supplementary marks to use as input features.
        log_tau_mean: Mean inter-event times in the dataset.
        log_tau_std: Standard deviation of the inter-event times in the dataset.
        mag_mean: Mean earthquake magnitude in the dataset.
        history_size: Size of the RNN hidden state, or history embedding.
        num_dist_components: Number of individual component distributions in the output mixture distribution.
        dropout_prob: Dropout probability.
        learning_rate: Learning rate used in optimization.
        learning_decay_rate: The epoch-rate of decay for the learning rate.
        encoder_type: Type of encoder architecture. Possible choices {'GRU', 'RNN', 'LSTM', 'None'}
        decoder_type: Type of decoder architecture. Possible choices {'FCN', 'Trans'}
    """

    def __init__(
        self,
        input_magnitude: bool = True,
        input_injection: bool = True,
        train_to_forecast: bool = False,
        supplementary_mark_list: Optional[str] = [],
        log_tau_mean: float = 0.0,
        log_tau_std: float = 2.0,
        mag_mean: float = 0.0,
        history_size: int = 8, # (Dh)
        num_dist_components: int = 1, # (Dt)
        dropout_prob: float = 0.2,
        learning_rate: float =1e-2,
        learning_decay_rate: float = 0.25,
        encoder_type = 'GRU',
        decoder_type = 'FCN',
        ):
        super().__init__()

        # Initialize.
        self.input_injection = input_injection
        self.input_magnitude = input_magnitude
        self.train_to_forecast = train_to_forecast
        self.history_size = history_size
        self.num_dist_components = num_dist_components
        self.learning_rate = learning_rate
        self.learning_decay_rate = learning_decay_rate
        self.encoder_type = encoder_type
        self.decoder_type = decoder_type
        self.register_buffer('log_tau_mean', torch.tensor(log_tau_mean, dtype=torch.float32))
        self.register_buffer('log_tau_std', torch.tensor(log_tau_std, dtype=torch.float32))
        self.register_buffer('mag_mean', torch.tensor(mag_mean, dtype=torch.float32))

        # Handling the supplementary marks.
        self.supplementary_mark_list = supplementary_mark_list
        self.num_supp_marks = len(supplementary_mark_list)

        # Encoder input mark and context sizes.
        self.num_marks = ( # (Dm)
            2  # Inter-event times & smoothed seismicity rate.
            + 2*int(self.input_magnitude)  # Magnitude & sequence marks.
            + 4*int(self.input_injection)  # Injection marks.
            + self.num_supp_marks # Supplementary marks.
            )
        self.context_size = self.num_marks + int(self.encoder_type!='None')*self.num_marks # (Dc)

        # Indicies of future-knowable marks to pass forward to the decoder for forecasting.
        # Note that this assumes injection/sequence marks have been turned on.
        PF_idx = [4,6,7,3] # vm, sv, dTS, Mc.

        # Encoder setup.
        if self.encoder_type != 'None':
            # Use a recurrent nerual network to encode the history embedding.
            self.rnn = eq.DL.IS_RNN_encoder(
                rnn_type = self.encoder_type, 
                d_model_in = self.num_marks, 
                #d_model_out = self.history_size, 
                dropout_prob = dropout_prob, 
                )

        # Decoder setup.
        if self.decoder_type == 'Trans':
            # Use a transformer for decoding the inter-event time distribution.
            self.decoder = eq.DL.IS_Transformer_decoder(
                d_modelDs = self.context_size, 
                d_modelDt = len(PF_idx), 
                d_model_out = self.num_dist_components, 
                nheadDs = self.num_marks, 
                nheadDt = 1, 
                dim_feedforward = self.context_size*2, 
                dropout_prob = dropout_prob, 
                F_idx = PF_idx
                )
        elif self.decoder_type == 'FCN' :
           # Use a fully-connected network for decoding the inter-event time distribution.
            self.decoder = eq.DL.IS_FCN_decoder(
                d_model_in = self.context_size, 
                d_model_ff = self.context_size, 
                d_model_out = self.num_dist_components, 
                lookback_size = 1, 
                dropout_prob = dropout_prob, 
                F_idx = PF_idx
                )

    def prep_time_marks(self, inter_times):
        # Pre-processing and error handling for the inter-event times.
        # inter_times has shape (...), output has shape (..., 1)
        log_tau = torch.log10(inter_times.clamp(1e-10,1e+10))
        return (log_tau.unsqueeze(-1) - self.log_tau_mean) / self.log_tau_std

    def prep_mag_marks(self, mag):
        # Pre-processing and error handling for the magnitude marks.
        # mag has shape (...), output has shape (..., 1)
        mag = mag.clamp(-10, +10)
        return mag.unsqueeze(-1) - self.mag_mean

    def prep_inj_marks(self, inj_mark):
        # Assuming that all injection marks have been adequately pre-processed.
        # inj_mark has shape (...), output has shape (..., 1)
        inj_mark = inj_mark.clamp(-10, +10)
        return inj_mark.unsqueeze(-1)

    def prep_supp_marks(self, supp_mark,mark_name):
        # Assuming that all supplementary marks have been adequately pre-processed.
        # supp_mark has shape (...), output has shape (..., 1)
        supp_mark = supp_mark.clamp(-10, +10)
        return supp_mark.unsqueeze(-1)

    def get_marks(self, batch):
        """ Get and prepare the input marks for every event in the batch.

        Returns:
            marks: The input marks, a tensor with shape (batch_size[B], seq_len[L], mark_size[Dm]).
        """
        # Create the input feature tensor from all of the flagged marks.
        mark_list = [self.prep_time_marks(batch.inter_times)]
        mark_list.append(self.prep_supp_marks(batch['aRs'],'aRs'))
        if self.input_magnitude:
            mark_list.append(self.prep_mag_marks(batch.mag))
            Mc=batch.mag_completeness * torch.ones_like(batch.mag)
            mark_list.append(self.prep_mag_marks(Mc))
        if self.input_injection:
            mark_list.append(self.prep_inj_marks(batch.vm))
            mark_list.append(self.prep_inj_marks(batch.dVc))
            mark_list.append(self.prep_inj_marks(batch.sv))
            mark_list.append(self.prep_inj_marks(batch.dTS))
        for mark in self.supplementary_mark_list:
            mark_list.append(self.prep_supp_marks(batch[mark],mark))
        marks = torch.cat(mark_list, dim=-1) # (B, L, Dm)

        return marks # (B, L, Dm)

    def get_dT(self, marks, history=None, forecasting=False, idx_split=None, use_injection=False):
        """ Estimate the mean inter-event times from the input marks.

        Returns:
            dT: OracleLite's estimates of the mean inter-event time, a tensor with shape (batch_size[B], seq_len[L],).
        """

        # Encode the marks into a history embedding and create the context embedding.
        if self.encoder_type != 'None':
            embedding = self.rnn(marks)[0]  # (B, L, Dh)
            embedding = torch.cat([marks,embedding],-1) # (B, L, Dc)
        else:
            embedding = marks

        # Decode the context embedding.
        log_dT = self.decoder.forward(embedding, forecasting=forecasting, idx=idx_split) # (B, L, 1)

        # Mean inter-event time formulation.
        log_dT = torch.tanh(log_dT)*5*2.302585093 # (B, L, 1)

        # Return the dT estimates, exponentiate to ensure positive and non-zero values.
        return log_dT.exp().squeeze(-1) # (B, L)

    def loss(self, batch: BatchIS, forecasting=False, forecast_count=0, add_rate_misfit=False) -> torch.Tensor:
        """ Compute the L1-norm of the (log10) inter-event time residuals.

        Args:
            batch: A batch of padded event sequences.

        Returns:
            Rloss: The L1-norm of (log10) residuals, shape (batch_size[B])
        """
        # Get the batch of dT estimates.
        marks = self.get_marks(batch)  # (B, L, Dm)
        dTpred = self.get_dT(marks).log10()[:,0:-2] # (B, L-2)

        # Compute the L1 norm of the residuals.
        dTobs = batch.inter_times[:,1:-1].clamp(1e-10,1e+10).log10() # (B, L-2)
        mask = batch.mask[:,1:-1] # (B, L-2)
        Rloss = ((dTpred-dTobs)*mask).norm(p=1,dim=-1) # (B)

        # Compute additional forecasting losses, if flagged to.
        if forecasting:

            # Handling the number of forecast realizations.
            if forecast_count==0:
                idx_list = range(1, batch.seq_len-1)
                forecast_count = batch.end_idx
            else:
                idx_list = random.sample(range(1, batch.seq_len-1),forecast_count)

            # Compute the loss for each forecast realization.
            for i in idx_list:
                dTpredi = self.get_dT(marks,forecasting=True, idx_split=i).log10() # (B, L-i-1)
                dTpredf = torch.cat([dTpred[:,0:i],dTpredi[:,0:-2]],dim=1) # (B, L-2)
                Rloss = Rloss + ((dTpredf-dTobs)*mask).norm(p=1,dim=-1) # (B)

            # Consider the average loss amongst all forecast realizations.
            Rloss = Rloss / (forecast_count + 1)

        # Return an event normalized loss.
        return Rloss / (batch.end_idx)  # (B)

    def evaluate_intensity(
        self,
        sequence: SequenceIS,
        num_grid_points: int = 0, # Ngp
        eps: float = 1e-10,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """ Evaluate the rate of seismicity (i.e., the intensity) for a given sequence.
        """
        # Not required for OracleLite.
        return None

    def evaluate_compensator(
        self,
        sequence: SequenceIS,
        num_grid_points: int = 10, # Ngp
        eps: float = 1e-10,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """ Evaluate the cumulative survival function of seismicity (i.e., the compensator) for a given sequence.
        """
        # Not required for OracleLite.
        return None

    def sample(
        self,
        sequence: SequenceIS,
        t_start: float,
        t_end: float,
        batch_size: int = 10,
        b: float = 1.0,
        return_sequences: bool = False,
        update_history: bool = False,
        eps: float = 1e-10,
    ) -> Union[BatchIS, List[SequenceIS]]:
        """ Sample a batch of events from the model.
        """
        # Not required for OracleLite.
        return None

    def interpolate_injection(self, arrival_times, sequence):
        """ Simple subroutine to interpolate injection marks."""
        vm = torch.from_numpy( np.interp(arrival_times.numpy(), sequence.arrival_times.numpy(), sequence.vm.numpy() ))
        dVc = torch.from_numpy(np.interp(arrival_times.numpy(), sequence.arrival_times.numpy(), sequence.dVc.numpy() ))
        sv = torch.from_numpy(np.interp(arrival_times.numpy(), sequence.arrival_times.numpy(), sequence.sv.numpy() ))
        dTS = torch.from_numpy(np.interp(arrival_times.numpy(), sequence.arrival_times.numpy(), sequence.dTS.numpy() ))
        return vm.float(), dVc.float(), sv.float(), dTS.float()


