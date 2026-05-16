from __future__ import annotations

import torch
import torch.nn as nn

from ml.src.models.item_tower import ItemTower
from ml.src.models.user_tower import UserTower


class TwoTowerModel(nn.Module):
    def __init__(
        self,
        num_users: int,
        num_items: int,
        embed_dim: int = 128,
    ) -> None:
        super().__init__()
        self.user_tower = UserTower(num_users=num_users, output_dim=embed_dim)
        self.item_tower = ItemTower(num_items=num_items, output_dim=embed_dim)
        self.temperature = nn.Parameter(torch.tensor(0.07))

    def forward(
        self,
        user_ids: torch.Tensor,
        item_ids: torch.Tensor,
        history_emb: torch.Tensor,
        genre_affinity: torch.Tensor,
        genre_vec: torch.Tensor,
        numeric_feats: torch.Tensor,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        user_emb = self.user_tower(user_ids, history_emb, genre_affinity)
        item_emb = self.item_tower(item_ids, genre_vec, numeric_feats)
        return user_emb, item_emb

    def compute_logits(self, user_emb: torch.Tensor, item_emb: torch.Tensor) -> torch.Tensor:
        return (user_emb @ item_emb.T) / self.temperature.clamp(min=1e-4)
