from typing import Optional, Tuple

import pytorch_lightning as pl
import torch

import eq


class TPPModel(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.save_hyperparameters()

    def loss(self, batch: eq.data.BatchIS) -> torch.Tensor:
        """ Compute negative log-likelihood (NLL) for a batch of event sequences.

        Args:
            batch: BatchIS of padded event sequences.

        Returns:
            nll: NLL of each sequence, shape (batch_size,)
        """
        raise NotImplementedError

    def sample(
        self,
        batch_size: int,
        duration: float,
        t_start: float = 0.0,
        past_seq: Optional[eq.data.SequenceIS] = None,
    ) -> eq.data.BatchIS:
        """ Sample a batch of sequences from the TPP model.

        Args:
            batch_size: Number of sequences to generate.
            duration: Length of the time interval on which the sequence is simulated.

        Returns:
            batch: BatchIS of padded event sequences.
        """
        raise NotImplementedError

    def evaluate_intensity(
        self, sequence: eq.data.SequenceIS, num_grid_points: int = 50
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """ Evaluate the intensity for the given sequence (used for plotting).

        Args:
            sequence: Sequence for which to evaluate the intensity.
            num_grid_points: Number of points between consecutive events on which to
                evaluate the intensity.

        Returns:
            grid: Times for which the intensity is evaluated,
                shape (seq_len * num_grid_points,)
            intensity: Values of the conditional intensity on times in grid,
                shape (seq_len * num_grid_points,)
        """
        raise NotImplementedError

    def evaluate_compensator(
        self, sequence: eq.data.SequenceIS, num_grid_points: int = 50
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """ Evaluate the compensator for the given sequence (used for plotting).

        Args:
            sequence: Sequence for which to evaluate the compensator.
            num_grid_points: Number of points between consecutive events on which to
                evaluate the compensator.

        Returns:
            grid: Times for which the intensity is evaluated,
                shape (seq_len * num_grid_points,)
            intensity: Values of the conditional intensity on times in grid,
                shape (seq_len * num_grid_points,)
        """
        raise NotImplementedError

    def training_step(self, batch, batch_idx):
        fit_loss = self.loss(batch, add_rate_misfit=False).mean(dim=0)
        loss = fit_loss
        self.log(
            "train_fit_loss",
            fit_loss.detach().item(),
            on_step=False,
            on_epoch=True,
            batch_size=batch.batch_size,
        )
        if hasattr(self, "train_to_forecast"):
            if self.train_to_forecast:
                forecast_loss = self.loss(batch, forecasting=True, forecast_count=5, add_rate_misfit=False).mean(dim=0)
                loss = forecast_loss
                fit_loss = fit_loss.detach()
                self.log(
                    "train_forecast_loss",
                    forecast_loss.detach().item(),
                    on_step=False,
                    on_epoch=True,
                    batch_size=batch.batch_size,
                )
        return loss

    def validation_step(self, batch, batch_idx):
        with torch.no_grad():
            fit_loss = self.loss(batch, add_rate_misfit=False).mean(dim=0)
            self.log(
                "val_fit_loss",
                fit_loss.detach().item(),
                on_step=False,
                on_epoch=True,
                prog_bar=True,
                batch_size=batch.batch_size,
            )
            if hasattr(self, "train_to_forecast"):
                if self.train_to_forecast:
                    forecast_loss = self.loss(batch, forecasting=True, forecast_count=5, add_rate_misfit=False).mean(dim=0)
                    fit_loss = fit_loss.detach()
                    self.log(
                        "val_forecast_loss",
                        forecast_loss.detach().item(),
                        on_step=False,
                        on_epoch=True,
                        batch_size=batch.batch_size,
                    )

    def on_after_backward(self) -> None:
        valid_gradients = True
        for param in self.parameters():
            if param.grad is not None:
                valid_gradients = not (torch.isnan(param.grad).any() or torch.isinf(param.grad).any())
                if not valid_gradients:
                    print('NaN gradient issues.')
                    param.grad = torch.nan_to_num(param.grad,nan=0.0,posinf=0.0,neginf=0.0)
    
    def on_before_optimizer_step(self, optimizer):
        norm_order = 2.0 
        norms = pl.utilities.grad_norm(self, norm_type=norm_order)
        self.log('Total gradient (norm)',norms[f'grad_{norm_order}_norm_total'],on_step=False,on_epoch=True)

    def test_step(self, batch, batch_idx, dataset_idx=None):
        with torch.no_grad():
            fit_loss = self.loss(batch).mean()
            self.log(
                "test_fit_loss",
                fit_loss.detach().item(),
                on_step=False,
                on_epoch=True,
                batch_size=batch.batch_size,
            )
            if hasattr(self, "train_to_forecast"):
                if self.train_to_forecast:
                    forecast_loss = self.loss(batch, forecasting=True, forecast_count=10).mean(dim=0)
                    fit_loss = fit_loss.detach()
                    self.log(
                        "test_forecast_loss",
                        forecast_loss.detach().item(),
                        on_step=False,
                        on_epoch=True,
                        batch_size=batch.batch_size,
                    )

    def configure_optimizers(self):
        if hasattr(self, "learning_rate"):
            lr = self.learning_rate
        else:
            lr = 1e-3
        if hasattr(self, "learning_decay_rate"):
            dr = self.learning_decay_rate
        else:
            dr = 0
        
        if dr != 0:
            optimizer = torch.optim.Adam(self.parameters(), lr=lr)
            scheduler = [torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda=self.lr_decay_fxn)]
            #scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, factor=dr, patience=5)
            #scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=1, T_mult=2)
        else:
            optimizer = torch.optim.Adam(self.parameters(), lr=lr)
            scheduler=[]
        return [optimizer],scheduler

    def lr_decay_fxn(self, epoch):
        return max( (epoch+1) ** -self.learning_decay_rate, 1e-3 )