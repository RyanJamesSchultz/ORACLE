import torch
import torch.nn as nn
import torch.nn.functional as F

from torch.distributions import Categorical
import eq.distributions as dist



class dist_decoder(nn.Module):
    """ Recurrent neural network (RNN) for encoding IS sequences into an embedding history."""

    def __init__(self, 
        num_dist_components = 32,
        ):
        super().__init__()

        # Initialize.
        self.num_dist_components = num_dist_components # (Dt)

    def forward(self, inp,):
        """ Decode the inter-event time distribution."""
        # Compute the necessary parameters for the mixture distribution.
        log_mean, shape, weight_logits = torch.split(
            inp,
            [self.num_dist_components, self.num_dist_components, self.num_dist_components],
            dim=-1,
        )
        log_mean = torch.tanh(log_mean)*5*2.302585093 # (B, L, Dt)
        shape = F.softplus(shape).clamp(1e-1,1e+2) # (B, L, Dt)
        weight_logits = F.log_softmax(weight_logits, dim=-1) # (B, L, Dt)

        # Make the components of the mixture distribution.
        component_dist = dist.Weibull(log_mean=log_mean, shape=shape) # (B, L, Dt)
        mixture_dist = Categorical(logits=weight_logits)

        # Return the dT distribution.
        return dist.MixtureSameFamily(
            mixture_distribution=mixture_dist,
            component_distribution=component_dist,
        )

