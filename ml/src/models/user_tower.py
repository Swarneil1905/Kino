from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class UserTower(nn.Module):
    def __init__(
        self,
        num_users: int,
        user_emb_dim: int = 64,
        genre_dim: int = 18,
        history_dim: int = 64,
        hidden: int = 256,
        output_dim: int = 128,
    ) -> None:
        super().__init__()
        self.user_embedding = nn.Embedding(num_users, user_emb_dim)
        input_dim = user_emb_dim + history_dim + genre_dim
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.BatchNorm1d(hidden),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden, hidden),
            nn.BatchNorm1d(hidden),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden, output_dim),
        )

    def forward(
        self,
        user_ids: torch.Tensor,
        history_emb: torch.Tensor,
        genre_affinity: torch.Tensor,
    ) -> torch.Tensor:
        user_emb = self.user_embedding(user_ids)
        x = torch.cat([user_emb, history_emb, genre_affinity], dim=-1)
        out = self.mlp(x)
        return F.normalize(out, p=2, dim=-1)
