from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class ItemTower(nn.Module):
    def __init__(self, num_items: int, genre_dim: int = 18, embed_dim: int = 128) -> None:
        super().__init__()
        self.item_embedding = nn.Embedding(num_items, 64)
        input_dim = 64 + genre_dim + 2
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

    def forward(self, item_ids: torch.Tensor, genre_vec: torch.Tensor, numeric_feats: torch.Tensor) -> torch.Tensor:
        x = torch.cat([self.item_embedding(item_ids), genre_vec, numeric_feats], dim=-1)
        return F.normalize(self.mlp(x), p=2, dim=-1)
