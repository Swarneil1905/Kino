from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F


class ItemTower(nn.Module):
    def __init__(
        self,
        num_items: int,
        item_emb_dim: int = 64,
        genre_dim: int = 18,
        numeric_dim: int = 2,
        hidden: int = 256,
        output_dim: int = 128,
    ) -> None:
        super().__init__()
        self.item_embedding = nn.Embedding(num_items, item_emb_dim)
        input_dim = item_emb_dim + genre_dim + numeric_dim
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
        item_ids: torch.Tensor,
        genre_vec: torch.Tensor,
        numeric_feats: torch.Tensor,
    ) -> torch.Tensor:
        item_emb = self.item_embedding(item_ids)
        x = torch.cat([item_emb, genre_vec, numeric_feats], dim=-1)
        out = self.mlp(x)
        return F.normalize(out, p=2, dim=-1)
