"""
Service for querying the EVE SDE SQLite database.
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from ..config import settings


class SDEService:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.sde_path
        self._conn = None

    def _get_connection(self):
        if self._conn is None:
            if not Path(self.db_path).exists():
                raise FileNotFoundError(f"SDE database not found at {self.db_path}")
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def get_blueprint_materials(
        self, blueprint_type_id: int, activity_id: int = 1
    ) -> List[Dict]:
        """
        Get materials required to manufacture a blueprint.
        activity_id=1 is manufacturing.
        Returns list of {typeID, quantity}
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT materialTypeID as typeID, quantity
            FROM industryActivityMaterials
            WHERE typeID = ? AND activityID = ?
            """,
            (blueprint_type_id, activity_id),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_blueprint_products(self, blueprint_type_id: int) -> List[Dict]:
        """
        Get what a blueprint produces (output products).
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT productTypeID as typeID, quantity
            FROM industryActivityProducts
            WHERE typeID = ? AND activityID = 1
            """,
            (blueprint_type_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_blueprint_by_product(self, product_type_id: int) -> Optional[int]:
        """
        Find the blueprint that produces this product.
        Returns blueprint_type_id or None.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT typeID as blueprintTypeID
            FROM industryActivityProducts
            WHERE productTypeID = ? AND activityID = 1
            LIMIT 1
            """,
            (product_type_id,),
        )
        row = cursor.fetchone()
        return row["blueprintTypeID"] if row else None

    def get_type_info(self, type_id: int) -> Optional[Dict]:
        """
        Get item name, group, and other basic info.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT typeID, typeName, groupID
            FROM invTypes
            WHERE typeID = ?
            """,
            (type_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def search_systems(self, name_query: str, limit: int = 20) -> List[Dict]:
        """Search solar systems by name."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT solarSystemID, solarSystemName, security
            FROM mapSolarSystems
            WHERE solarSystemName LIKE ?
            ORDER BY
                CASE WHEN solarSystemName = ? THEN 0
                     WHEN solarSystemName LIKE ? THEN 1
                     ELSE 2 END,
                solarSystemName
            LIMIT ?
            """,
            (f"%{name_query}%", name_query, f"{name_query}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_type_names(self, type_ids: List[int]) -> Dict[int, str]:
        """Bulk lookup of type names. Returns {type_id: type_name}."""
        if not type_ids:
            return {}
        conn = self._get_connection()
        placeholders = ",".join("?" * len(type_ids))
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT typeID, typeName FROM invTypes WHERE typeID IN ({placeholders})",
            type_ids,
        )
        return {row["typeID"]: row["typeName"] for row in cursor.fetchall()}

    def search_types(self, name_query: str, limit: int = 50) -> List[Dict]:
        """
        Search for types by name (case-insensitive).
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT typeID, typeName, groupID
            FROM invTypes
            WHERE typeName LIKE ?
            ORDER BY
                CASE
                    WHEN typeName = ? THEN 0
                    WHEN typeName LIKE ? THEN 1
                    ELSE 2
                END,
                typeName
            LIMIT ?
            """,
            (f"%{name_query}%", name_query, f"{name_query}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_required_skills(self, blueprint_type_id: int) -> List[Dict]:
        """
        Get skills required to manufacture a blueprint.
        Returns list of {typeID (skill), level}
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT skillID as typeID, level
            FROM industryActivitySkills
            WHERE typeID = ? AND activityID = 1
            """,
            (blueprint_type_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Singleton instance
_sde_service = None


def get_sde_service() -> SDEService:
    global _sde_service
    if _sde_service is None:
        _sde_service = SDEService()
    return _sde_service
