from pydantic import BaseModel
from typing import List, Dict, Optional


class ManufacturingRequest(BaseModel):
    product_type_id: int
    runs: int = 1
    me_level: int = 0
    structure_bonus: float = 0.01
    rig_bonus: float = 0.02
    build_intermediates: bool = True


class CostSummary(BaseModel):
    material_cost: float
    install_cost: float
    total_cost: float
    jita_sell_price: float
    margin: float
    margin_percent: float


class MaterialTreeNode(BaseModel):
    type_id: int
    type_name: str
    quantity_needed: float
    quantity_owned: float = 0.0
    quantity_to_buy: float
    unit_price: float
    total_cost: float
    is_buildable: bool
    me_level: int = 0
    children: List["MaterialTreeNode"] = []

    class Config:
        populate_by_name = True


MaterialTreeNode.model_rebuild()


class ManufacturingResponse(BaseModel):
    product: Dict
    runs: int
    me_level: int
    material_tree: MaterialTreeNode
    flat_materials: List[MaterialTreeNode]
    cost_summary: CostSummary
