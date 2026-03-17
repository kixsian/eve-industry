#!/usr/bin/env python3
"""
Create a minimal test SDE database with a few key blueprints for smoke testing.
Includes: Rifter, basic materials
"""
import sqlite3
from pathlib import Path

SDE_DIR = Path(__file__).parent.parent / "sde"
SDE_DB = SDE_DIR / "eve.db"

def create_test_sde():
    SDE_DIR.mkdir(exist_ok=True)

    # Remove existing test DB
    if SDE_DB.exists():
        SDE_DB.unlink()

    conn = sqlite3.connect(SDE_DB)
    cursor = conn.cursor()

    # Create minimal SDE schema
    cursor.execute("""
    CREATE TABLE invTypes (
        typeID INTEGER PRIMARY KEY,
        typeName TEXT NOT NULL,
        groupID INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE industryActivityProducts (
        blueprintTypeID INTEGER,
        productTypeID INTEGER,
        typeID INTEGER,
        quantity INTEGER,
        activityID INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE industryActivityMaterials (
        blueprintTypeID INTEGER,
        materialTypeID INTEGER,
        typeID INTEGER,
        quantity INTEGER,
        activityID INTEGER
    )
    """)

    cursor.execute("""
    CREATE TABLE industryActivitySkills (
        blueprintTypeID INTEGER,
        typeID INTEGER,
        level INTEGER,
        activityID INTEGER
    )
    """)

    # Insert test data: Rifter and components
    # Rifter blueprint = 587, Rifter ship = 587
    items = [
        (587, "Rifter", 6),              # Rifter (frigate)
        (598, "Rifter Blueprint", 9),    # Rifter Blueprint
        (34, "Tritanium", 18),           # Raw material
        (35, "Pyerite", 18),             # Raw material
        (36, "Mexallon", 18),            # Raw material
        (37, "Isogen", 18),              # Raw material
        (38, "Nocxium", 18),             # Raw material
        (39, "Zydrine", 18),             # Raw material
        (40, "Megacyte", 18),            # Raw material
        (11399, "Compressed Scordite", 18),  # Raw
        (1, "Civilian Damage Control", 24),  # Module
    ]

    for type_id, name, group_id in items:
        cursor.execute(
            "INSERT INTO invTypes (typeID, typeName, groupID) VALUES (?, ?, ?)",
            (type_id, name, group_id)
        )

    # Rifter Blueprint produces Rifter (1 per run)
    cursor.execute(
        """INSERT INTO industryActivityProducts
           (blueprintTypeID, productTypeID, typeID, quantity, activityID)
           VALUES (?, ?, ?, ?, ?)""",
        (598, 587, 587, 1, 1)  # blueprint 598 makes 1x Rifter (587)
    )

    # Rifter Blueprint materials (simplified)
    rifter_materials = [
        (598, 34, 1500),   # 1500 Tritanium
        (598, 35, 300),    # 300 Pyerite
        (598, 36, 250),    # 250 Mexallon
        (598, 37, 50),     # 50 Isogen
    ]

    for blueprint_id, material_id, quantity in rifter_materials:
        cursor.execute(
            """INSERT INTO industryActivityMaterials
               (blueprintTypeID, materialTypeID, typeID, quantity, activityID)
               VALUES (?, ?, ?, ?, ?)""",
            (blueprint_id, material_id, material_id, quantity, 1)
        )

    # Rifter Blueprint requires skills
    cursor.execute(
        """INSERT INTO industryActivitySkills
           (blueprintTypeID, typeID, level, activityID)
           VALUES (?, ?, ?, ?)""",
        (598, 3309, 1, 1)  # Small Ship Construction I
    )

    conn.commit()
    conn.close()

    print(f"✓ Test SDE created at {SDE_DB}")
    print("  - Rifter (587): Blueprint 598 → 1 Rifter per run")
    print("  - Materials: Tritanium, Pyerite, Mexallon, Isogen")


if __name__ == "__main__":
    create_test_sde()
