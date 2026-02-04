import torch
import torch.nn as nn
import torch.nn.functional as F



class IS_RNN_encoder(nn.Module):
    """ Recurrent neural network (RNN) for encoding IS sequences into an embedding history."""

    def __init__(self, 
        rnn_type: str = 'GRU',
        d_model_in: int = 8,  # (Di)
        #d_model_out: int = 8, # (Do)
        num_layers: int = 1, 
        dropout_prob: float = 0.2, 
        batch_first: bool = True,
        ):
        super().__init__()

        # Check for valid RNN type flags.
        if rnn_type not in ['RNN', 'GRU', 'LSTM']:
            raise ValueError(
                f"rnn_type must be one of ['RNN', 'GRU', 'LSTM'] " f"(got {rnn_type})"
            )

        # Initialize.
        self.rnn = getattr(nn, rnn_type)( d_model_in, d_model_in, num_layers=num_layers, dropout=dropout_prob, batch_first=batch_first, )
        self.dropout = nn.Dropout(dropout_prob)
        self.normH = nn.LayerNorm(d_model_in)

    def forward(self, inp, hidden=None):
        """ Apply the RNN encoder to the input tensor."""
        out, hidden = self.rnn(inp,hidden)
        return self.normH(self.dropout(out)+inp), hidden # (B, L, Di), (num_layers, B, Di)



class IS_FCN_decoder(nn.Module):
    """ Fully connected network (FCN) for decoding IS sequences."""

    def __init__(
        self, 
        d_model_in: int = 8,  # (Di)
        d_model_ff: int = 32, # (Dh)
        d_model_out: int = 1, # (Do)
        lookback_size: int = 1, # (Dl)
        num_Hlayers: int = 1, 
        dropout_prob: float = 0.2, 
        F_idx = None,
        ):
        super().__init__()

        # Initialize.
        d_model_1 = d_model_in*lookback_size+len(F_idx)+1 # (D1)
        self.F_idx = F_idx
        self.lookback_size = lookback_size
        self.first = nn.Linear(d_model_1, d_model_ff)
        self.FCN_A1 = nn.PReLU(1)
        self.FCN_Hlayers = nn.ModuleList([nn.Linear(d_model_ff,d_model_ff) for _ in range(num_Hlayers)])
        self.FCN_Ah = nn.ModuleList([nn.PReLU(1) for _ in range(num_Hlayers)])
        self.dropout = nn.Dropout(dropout_prob)
        self.final = nn.Linear(d_model_ff, d_model_out)

    def forward(self, inp, forecasting=False, idx=0, val=-10.0):
        """ Apply the FCN decoder to the input tensor."""

        # Apply a lookback to the history of marks.
        if self.lookback_size>1:
            inp = self.apply_lookback(inp, val) # (B, L, Di*Dl)

        # Prep input data.
        inp = self.prep_data(inp, forecasting=forecasting,idx=idx) # (B, L, D1)

        # Apply the FCN to the input data.
        inp = self.FCN_A1(self.dropout(self.first(inp))) # (B, L, Df)
        for layer, activation in zip(self.FCN_Hlayers, self.FCN_Ah):
            inp = activation(self.dropout(layer(inp))) # (B, L, Df)

        # Apply the final layer and return the output.
        return self.final(self.dropout(inp)) # (B, L, Do)

    def apply_lookback(self, inp, val):
        """ Apply lookback to the input tensor."""

        # Prep and pad.
        Li=inp.shape[1]
        inp=F.pad(inp,(0,0,self.lookback_size,0),value=val)

        # Loop over the lookback length, appending prior history embeddings.
        element_list = []
        for i in range(self.lookback_size):
            element_list.append(inp[:,(0+i):(Li+i),:])

        # Concatenate and return.
        out=torch.cat(element_list,dim=-1)
        return out # (B, L, Di*Dl)

    def prep_data(self, inp, forecasting=False, idx=0):
        """ Prepare the input tensor."""

        # Append the forecasting flag and current injection marks to the input history marks.
        if not forecasting:
            out = inp
            forecast_flag = 0 * torch.ones_like(out[:,:,[0]])
            Fmarks = inp[:,:,self.F_idx]
        else:
            sequence_length = inp.shape[1]
            out=inp[:,[idx-1],:]
            out=out.expand(-1,sequence_length-idx,-1)
            forecast_flag = 1 * torch.ones_like(out[:,:,[0]])
            Fmarks = inp[:,idx:,self.F_idx]

        # Append the forecasting flag and forecasting marks, then return.
        return torch.cat([out,forecast_flag,Fmarks],dim=-1) # (B, L, Di+1+3)



class IS_Transformer_decoder(nn.Module):
    """ Transformer architecture for decoding IS sequences."""

    def __init__(self, 
        d_modelDs: int = 16,  # (Ds)
        d_modelDt: int = 3,   # (Dt)
        d_model_out: int = 1, # (Do)
        nheadDs: int = 4,
        nheadDt: int = 3,
        num_Dslayers: int = 1, 
        num_Dtlayers: int = 1, 
        dim_feedforward: int = 32, 
        dropout_prob: float = 0.2, 
        batch_first: bool = True,
        F_idx = None,
        ):
        super().__init__()

        # Initialize.
        self.F_idx = F_idx
        self.Ds_layers = nn.ModuleList([nn.TransformerEncoderLayer(d_model=d_modelDs,nhead=nheadDs,dim_feedforward=dim_feedforward, dropout=dropout_prob, activation='gelu', batch_first=batch_first) for _ in range(num_Dslayers)])
        self.Dt_layers = nn.ModuleList([nn.TransformerDecoderLayer(d_model=d_modelDt,nhead=nheadDt,dim_feedforward=dim_feedforward, dropout=dropout_prob, activation='gelu', batch_first=batch_first) for _ in range(num_Dtlayers)])
        self.dropout = nn.Dropout(dropout_prob)
        self.B_layer = nn.Linear(d_modelDs, d_modelDt)
        self.Fs_layer = nn.Linear(d_modelDs, d_model_out)
        self.Ff_layer = nn.Linear(d_modelDt, d_model_out)

    def forward(self, inp, forecasting=False, idx=0):
        """ Apply the Transformer decoder to the input tensor."""

        # Prep the data.
        src, tgt = self.prep_data(inp,forecasting=forecasting,idx=idx) # (B, Ls, Ds), (B, Lt, Dt)

        # Handle causality.
        if not forecasting:
            causal_mask = nn.Transformer.generate_square_subsequent_mask(src.shape[1]) # (B, Ls, Ls)
            causal_flag = True
        else:
            causal_mask = None
            causal_flag = False

        # Apply the history decoder.
        for Ds_layer in self.Ds_layers:
            src = Ds_layer(src, is_causal=causal_flag, src_mask=causal_mask) # (B, Ls, Ds)

        # Apply the target decoder.
        if not forecasting:
            out = self.Fs_layer(self.dropout(src)) # (B, Ls, Do)
        else:
            src = self.B_layer(src) # (B, Ls, Dt)
            for Dt_layer in self.Dt_layers:
                tgt = Dt_layer(tgt,src, tgt_mask=causal_mask, memory_mask=causal_mask, tgt_is_causal=causal_flag, memory_is_causal=causal_flag) # (B, Lt, Dt)
            out = self.Ff_layer(self.dropout(tgt)) # (B, Lt, Do)  

        # Return the output.
        return out # (B, Ls/Lt, Do)

    def prep_data(self, inp, forecasting=False, idx=0):
        """ Prepare the input tensor."""

        # Split the data into source and target tensors.
        if not forecasting:
            src = inp[:,:,:]          # (B, L, Ds)
            tgt = inp[:,:,self.F_idx] # (B, L, Dt)
        else:
            src = inp[:,0:idx,:]         #(B,   idx, Ds)
            tgt = inp[:,idx:,self.F_idx] #(B, L-idx, Dt)

        # Return.
        return src, tgt


