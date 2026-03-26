from fastapi import APIRouter, HTTPException, Depends
from ..schemas.manufacturing import ManufacturingRequest, ManufacturingResponse
from ..services.manufacturing_engine import ManufacturingEngine
from ..services.market_service import get_market_service
from ..services.sde_service import get_sde_service
from ..services.auth_service import get_current_character
from ..services import esi_service

router = APIRouter(prefix="/manufacturing", tags=["manufacturing"])


@router.post("/calculate", response_model=ManufacturingResponse)
async def calculate_manufacturing(request: ManufacturingRequest):
    """
    Calculate manufacturing costs and material breakdown.
    """
    try:
        sde = get_sde_service()
        market = await get_market_service()
        engine = ManufacturingEngine(sde)

        # Build the tree first to get all type IDs
        tree = engine.build_material_tree(
            request.product_type_id,
            1.0,  # quantity
            request.runs,
            me_level=request.me_level,
            structure_bonus=request.structure_bonus,
            rig_bonus=request.rig_bonus,
            build_intermediates=request.build_intermediates,
        )

        # Collect all type IDs from tree
        def collect_type_ids(node):
            ids = {node.type_id}
            for child in node.children:
                ids.update(collect_type_ids(child))
            return ids

        type_ids = list(collect_type_ids(tree))

        # Fetch prices
        prices = await market.get_prices(type_ids)

        # Fetch corp assets if authenticated
        owned = {}
        if get_current_character():
            try:
                owned = await esi_service.get_corp_asset_quantities()
            except Exception:
                pass  # Not authenticated or no corp access — skip

        # Run full calculation with prices and owned quantities
        result = engine.calculate_manufacturing(
            request.product_type_id,
            1.0,  # quantity
            request.runs,
            me_level=request.me_level,
            structure_bonus=request.structure_bonus,
            rig_bonus=request.rig_bonus,
            build_intermediates=request.build_intermediates,
            prices=prices,
            owned=owned,
        )

        # Convert to response format (convert camelCase dict keys)
        def convert_dict(d):
            if isinstance(d, dict):
                return {
                    "type_id": d.get("typeID"),
                    "type_name": d.get("typeName"),
                }
            return d

        response_tree = _convert_node_to_response(result["materialTree"])
        response_flat = [_convert_node_to_response(n) for n in result["flatMaterials"]]
        response_components = [_convert_node_to_response(n) for n in result["directComponents"]]
        cost_summary = {
            "material_cost": result["costSummary"]["materialCost"],
            "component_buy_cost": result["costSummary"]["componentBuyCost"],
            "install_cost": result["costSummary"]["installCost"],
            "total_cost": result["costSummary"]["totalCost"],
            "jita_sell_price": result["costSummary"]["jitaSellPrice"],
            "margin": result["costSummary"]["margin"],
            "margin_percent": result["costSummary"]["marginPercent"],
        }

        return ManufacturingResponse(
            product=result["product"],
            runs=result["runs"],
            me_level=result["meLevel"],
            material_tree=response_tree,
            flat_materials=response_flat,
            direct_components=response_components,
            cost_summary=cost_summary,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@router.get("/search")
async def search_items(q: str, limit: int = 50):
    """
    Search for items by name in the SDE.
    """
    try:
        sde = get_sde_service()
        results = sde.search_types(q, limit=limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _convert_node_to_response(node_dict: dict):
    """Convert manufacturing engine dict to response schema."""
    return {
        "type_id": node_dict["typeID"],
        "type_name": node_dict["typeName"],
        "quantity_needed": node_dict["quantityNeeded"],
        "quantity_owned": node_dict["quantityOwned"],
        "quantity_to_buy": node_dict["quantityToBuy"],
        "unit_price": node_dict["unitPrice"],
        "total_cost": node_dict["totalCost"],
        "is_buildable": node_dict["isBuildable"],
        "me_level": node_dict["meLevel"],
        "children": [_convert_node_to_response(child) for child in node_dict["children"]],
    }
