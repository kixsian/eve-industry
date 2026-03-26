"""
Manufacturing calculation engine with recursive material breakdown.
"""
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from .sde_service import SDEService


@dataclass
class MaterialNode:
    """Represents a material or component in the manufacturing tree."""
    type_id: int
    type_name: str
    quantity_needed: float
    quantity_owned: float = 0.0
    unit_price: float = 0.0
    children: List["MaterialNode"] = field(default_factory=list)
    is_buildable: bool = False
    me_level: int = 0
    structure_bonus: float = 0.01  # Engineering Complex 1% base
    rig_bonus: float = 0.02  # T1 Rig 2% in highsec

    @property
    def quantity_needed_adjusted(self) -> float:
        """Quantity after ME/structure/rig bonuses."""
        return self.quantity_needed

    @property
    def quantity_to_buy(self) -> float:
        """How much to buy from market (need - owned)."""
        return max(0, self.quantity_needed - self.quantity_owned)

    @property
    def total_cost(self) -> float:
        """Full cost of materials for this node (based on quantity needed, not to-buy)."""
        if self.children:
            return sum(child.total_cost for child in self.children)
        else:
            return self.quantity_needed * self.unit_price

    def to_dict(self) -> Dict:
        """Convert to dict for API response."""
        return {
            "typeID": self.type_id,
            "typeName": self.type_name,
            "quantityNeeded": self.quantity_needed,
            "quantityOwned": self.quantity_owned,
            "quantityToBuy": self.quantity_to_buy,
            "unitPrice": self.unit_price,
            "totalCost": self.total_cost,
            "isBuildable": self.is_buildable,
            "meLevel": self.me_level,
            "children": [child.to_dict() for child in self.children],
        }


class ManufacturingEngine:
    def __init__(self, sde_service: SDEService):
        self.sde = sde_service

    def calculate_adjusted_quantity(
        self,
        base_quantity: float,
        runs: int,
        me_level: int = 0,
        structure_bonus: float = 0.01,
        rig_bonus: float = 0.02,
    ) -> int:
        """
        Calculate adjusted material quantity with ME, structure, and rig bonuses.

        Formula:
        raw = base_qty * ((100 - me_level) / 100) * (1 - structure_bonus) * (1 - rig_bonus) * runs
        return max(runs, ceil(round(raw, 2)))
        """
        multiplier = ((100 - me_level) / 100) * (1 - structure_bonus) * (1 - rig_bonus)
        raw = base_quantity * multiplier * runs
        rounded = round(raw, 2)
        return max(runs, math.ceil(rounded))

    def build_material_tree(
        self,
        product_type_id: int,
        quantity_needed: float,
        runs: int,
        me_level: int = 0,
        structure_bonus: float = 0.01,
        rig_bonus: float = 0.02,
        build_intermediates: bool = True,
        _depth: int = 0,
        _max_depth: int = 20,
    ) -> MaterialNode:
        """
        Recursively build a material tree for manufacturing.

        Args:
            product_type_id: What we're making
            quantity_needed: How many units we need
            runs: Number of manufacturing runs
            me_level: Material Efficiency level (0-10)
            structure_bonus: Structure bonus (EC = 0.01)
            rig_bonus: Rig bonus (T1 = 0.02)
            build_intermediates: Whether to recurse into sub-components
            _depth: Current recursion depth (prevent infinite loops)
            _max_depth: Max recursion depth

        Returns:
            MaterialNode tree
        """
        if _depth > _max_depth:
            raise ValueError(f"Recursion depth exceeded {_max_depth}")

        # Get product info
        product_info = self.sde.get_type_info(product_type_id)
        if not product_info:
            raise ValueError(f"Type {product_type_id} not found in SDE")

        node = MaterialNode(
            type_id=product_type_id,
            type_name=product_info["typeName"],
            quantity_needed=quantity_needed,
            me_level=me_level,
            structure_bonus=structure_bonus,
            rig_bonus=rig_bonus,
        )

        # Check if this is a blueprint or a raw material
        blueprint_id = self.sde.get_blueprint_by_product(product_type_id)
        if not blueprint_id:
            # No blueprint → leaf node (raw material)
            node.is_buildable = False
            return node

        node.is_buildable = True

        # If we're not building intermediates at this recursion depth, stop here
        if not build_intermediates and _depth > 0:
            return node

        # Get blueprint materials
        materials = self.sde.get_blueprint_materials(blueprint_id)
        if not materials:
            # Blueprint has no materials somehow, treat as leaf
            return node

        # Get output per run from blueprint products
        products = self.sde.get_blueprint_products(blueprint_id)
        output_per_run = sum(p["quantity"] for p in products) if products else 1

        # How many runs do we need?
        runs_needed = math.ceil(quantity_needed / output_per_run)

        # Process each material
        for material in materials:
            material_type_id = material["typeID"]
            material_base_qty = material["quantity"]

            # Apply adjustments
            adjusted_qty = self.calculate_adjusted_quantity(
                material_base_qty,
                runs_needed,
                me_level=0,  # Sub-components default to ME=0 (user can override)
                structure_bonus=structure_bonus,
                rig_bonus=rig_bonus,
            )

            # Check if this material is buildable
            material_blueprint_id = self.sde.get_blueprint_by_product(material_type_id)
            material_is_buildable = material_blueprint_id is not None

            if build_intermediates and material_is_buildable:
                # Recurse: build the sub-component
                child_node = self.build_material_tree(
                    material_type_id,
                    adjusted_qty,
                    runs_needed,
                    me_level=0,  # Sub-components start at ME=0
                    structure_bonus=structure_bonus,
                    rig_bonus=rig_bonus,
                    build_intermediates=build_intermediates,
                    _depth=_depth + 1,
                    _max_depth=_max_depth,
                )
            else:
                # Leaf node: raw material or user chose not to build
                material_info = self.sde.get_type_info(material_type_id)
                child_node = MaterialNode(
                    type_id=material_type_id,
                    type_name=material_info["typeName"] if material_info else f"Type {material_type_id}",
                    quantity_needed=adjusted_qty,
                    is_buildable=material_is_buildable,
                    structure_bonus=structure_bonus,
                    rig_bonus=rig_bonus,
                )

            node.children.append(child_node)

        return node

    def flatten_materials(self, node: MaterialNode) -> Dict[int, MaterialNode]:
        """
        Flatten the tree: aggregate all leaf materials (what actually needs to be bought).
        Returns dict of {type_id: MaterialNode} with cumulative quantities.
        """
        flat: Dict[int, MaterialNode] = {}

        def traverse(n: MaterialNode):
            if not n.children or not n.is_buildable:
                # Leaf node or user-chosen not to build
                if n.type_id in flat:
                    flat[n.type_id].quantity_needed += n.quantity_needed
                else:
                    flat[n.type_id] = MaterialNode(
                        type_id=n.type_id,
                        type_name=n.type_name,
                        quantity_needed=n.quantity_needed,
                        unit_price=n.unit_price,
                        is_buildable=n.is_buildable,
                    )
            else:
                # Internal node: recurse into children
                for child in n.children:
                    traverse(child)

        traverse(node)
        return flat

    def apply_prices(
        self, node: MaterialNode, prices: Dict[int, float]
    ) -> None:
        """
        Recursively apply prices to the tree.
        """
        node.unit_price = prices.get(node.type_id, 0.0)
        for child in node.children:
            self.apply_prices(child, prices)

    def apply_owned(
        self, node: MaterialNode, owned: Dict[int, int]
    ) -> None:
        """
        Recursively apply owned quantities from corp assets to the tree.
        Owned stock reduces quantity_to_buy, which reduces total cost.
        """
        node.quantity_owned = min(owned.get(node.type_id, 0), node.quantity_needed)
        for child in node.children:
            self.apply_owned(child, owned)

    def calculate_manufacturing(
        self,
        product_type_id: int,
        quantity: float,
        runs: int,
        me_level: int = 0,
        structure_bonus: float = 0.01,
        rig_bonus: float = 0.02,
        build_intermediates: bool = True,
        prices: Dict[int, float] = None,
        owned: Dict[int, int] = None,
        adjusted_prices: Dict[int, float] = None,
        system_cost_index: float = 0.0,
        facility_tax_rate: float = 0.0,
    ) -> Dict:
        """
        Full manufacturing calculation.
        """
        prices = prices or {}
        owned = owned or {}
        adjusted_prices = adjusted_prices or {}

        # Build tree
        tree = self.build_material_tree(
            product_type_id,
            quantity,
            runs,
            me_level=me_level,
            structure_bonus=structure_bonus,
            rig_bonus=rig_bonus,
            build_intermediates=build_intermediates,
        )

        # Apply prices and owned quantities to the full tree
        self.apply_prices(tree, prices)
        if owned:
            self.apply_owned(tree, owned)

        # Flatten for shopping list and re-apply owned (lost during flattening)
        flat = self.flatten_materials(tree)
        if owned:
            for node in flat.values():
                node.quantity_owned = min(owned.get(node.type_id, 0), node.quantity_needed)

        # Build direct components list (first-level blueprint materials, bought off market)
        direct_components = []
        for child in tree.children:
            child_owned = min(owned.get(child.type_id, 0), child.quantity_needed)
            child_to_buy = max(0.0, child.quantity_needed - child_owned)
            direct_components.append(MaterialNode(
                type_id=child.type_id,
                type_name=child.type_name,
                quantity_needed=child.quantity_needed,
                quantity_owned=child_owned,
                unit_price=child.unit_price,
                is_buildable=child.is_buildable,
                me_level=child.me_level,
            ))
            # Manually set quantity_to_buy since it's a property
            direct_components[-1].quantity_owned = child_owned

        # Calculate costs based on full quantity needed (ignoring owned stock)
        total_cost = sum(node.quantity_needed * node.unit_price for node in flat.values())
        component_buy_cost = sum(c.quantity_needed * c.unit_price for c in direct_components)

        # Install cost = EIV × system cost index × (1 + facility tax)
        # EIV uses CCP's adjusted prices for input materials
        eiv = sum(
            adjusted_prices.get(node.type_id, 0.0) * node.quantity_needed
            for node in flat.values()
        )
        install_cost = eiv * system_cost_index * (1 + facility_tax_rate)
        total_sell_price = tree.unit_price * (runs * self._get_output_per_run(product_type_id))

        product_info = self.sde.get_type_info(product_type_id)
        product_name = product_info["typeName"] if product_info else f"Type {product_type_id}"

        return {
            "product": {
                "typeID": product_type_id,
                "typeName": product_name,
            },
            "runs": runs,
            "meLevel": me_level,
            "materialTree": tree.to_dict(),
            "flatMaterials": sorted(
                [node.to_dict() for node in flat.values()],
                key=lambda x: x["typeName"],
            ),
            "directComponents": sorted(
                [c.to_dict() for c in direct_components],
                key=lambda x: x["typeName"],
            ),
            "costSummary": {
                "materialCost": total_cost,
                "componentBuyCost": component_buy_cost,
                "installCost": install_cost,
                "totalCost": total_cost,
                "jitaSellPrice": total_sell_price,
                "margin": total_sell_price - total_cost,
                "marginPercent": (
                    ((total_sell_price - total_cost) / total_sell_price * 100)
                    if total_sell_price > 0
                    else 0
                ),
            },
        }

    def _get_output_per_run(self, product_type_id: int) -> int:
        """Get how many units this blueprint produces per run."""
        blueprint_id = self.sde.get_blueprint_by_product(product_type_id)
        if not blueprint_id:
            return 1
        products = self.sde.get_blueprint_products(blueprint_id)
        return sum(p["quantity"] for p in products) if products else 1
