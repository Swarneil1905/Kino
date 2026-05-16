from __future__ import annotations

import torch
import torch.nn as nn


class Ranker(nn.Module):
    """MLP reranker over user/item embeddings and interaction features."""

    INPUT_DIM = 387

    def __init__(self) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(self.INPUT_DIM, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(
        self,
        user_emb: torch.Tensor,
        item_emb: torch.Tensor,
        genre_score: torch.Tensor,
        log_pop: torch.Tensor,
        release_decade: torch.Tensor,
    ) -> torch.Tensor:
        interaction = user_emb * item_emb
        x = torch.cat(
            [user_emb, item_emb, interaction, genre_score.unsqueeze(-1), log_pop.unsqueeze(-1), release_decade.unsqueeze(-1)],
            dim=-1,
        )
        return self.net(x).squeeze(-1)
