"""
Provides static data maps for the expected hardware configuration of each hardware type
"""
# map of interface layouts
IFACE_LAYOUTS = {
    "layout_1": [
        {
            "name": "mcx2p0",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx2p1",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx3p0",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx3p1",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "oob",
            "type": "virtual",
            "description": "iDRAC Management Card",
            "tags": [{"name": "oob-ip"}],
        },
    ],
    "layout_2": [
        {
            "name": "mcx1p1",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx1p2",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx2p1",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx2p2",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx3p1",
            "type": "100gbase-x-qsfp28",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx3p2",
            "type": "100gbase-x-qsfp28",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx4p1",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx4p2",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx5p1",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx5p2",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx6p1",
            "type": "100gbase-x-qsfp28",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx6p2",
            "type": "100gbase-x-qsfp28",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx7p1",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx7p2",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx8p1",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx8p2",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx9p1",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "mcx9p2",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "oob",
            "type": "virtual",
            "description": "iDRAC Management Card",
            "tags": [{"name": "oob-ip"}],
        },
    ],
    "layout_3": [
        {
            "name": "enp24s0f0",
            "type": "10gbase-x-sfpp",
            "description": "Intel X540",
            "tags": [],
        },
        {
            "name": "oob",
            "type": "virtual",
            "description": "Out of Band Management Card",
            "tags": [{"name": "oob-ip"}],
        },
    ],
    "layout_4": [
        {
            "name": "enp24s0f0np0",
            "type": "10gbase-x-sfpp",
            "description": "Mellanox Connect-X 5",
            "tags": [],
        },
        {
            "name": "oob",
            "type": "virtual",
            "description": "Out of Band Management Card",
            "tags": [{"name": "oob-ip"}],
        },
    ],
}
# map server models to the interface layout to use
MODEL_TO_IFACE_LAYOUTS = {
    "R6515": "layout_1",
    "R440": "layout_1",
    "R7525": "layout_2",
    "LLN": "layout_3",
    "LUM": "layout_4",
}
# map old to new interface names
IFACE_MIGRATIONS = {
    "map_1": {
        "mcx2p0": "mcx1p1",
        "mcx2p1": "mcx1p2",
        "mcx3p0": "mcx2p1",
        "mcx3p1": "mcx2p2",
        "oob": "oob",
    }
}
# map server models to target models to migration maps to use
# 1st level keys are the source model
MODEL_TO_IFACE_MIGRATIONS = {
    "R6515": {
        "R7525": "map_1",
    },
    "R440": {
        "R7525": "map_1",
    },
}


def get_iface_layout_for_model(model):
    """Return interface layout for the specified hardware model"""
    return IFACE_LAYOUTS[MODEL_TO_IFACE_LAYOUTS[model]]


def get_iface_migration_map(src_model, dst_model):
    """Return the migration map for a migration from the specifed
    source model to the destination model."""
    return IFACE_MIGRATIONS[MODEL_TO_IFACE_MIGRATIONS[src_model][dst_model]]
