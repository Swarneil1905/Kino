from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class UserTower(nn.Module):
    def __init__(self, num_users: int, genre_dim: int = 18, embed_dim: int = 128) -> None:
        super().__init__()
        self.user_embedding = nn.Embedding(num_users, 64)
        input_dim = 64 + 64 + genre_dim
        self.mlp = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, embed_dim),
        )

    def forward(self, user_ids: torch.Tensor, history_emb: torch.Tensor, genre_affinity: torch.Tensor) -> torch.Tensor:
        x = torch.cat([self.user_embedding(user_ids), history_emb, genre_affinity], dim=-1)
        return F.normalize(self.mlp(x), p=2, dim=-1)
