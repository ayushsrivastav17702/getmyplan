PLAN_FEATURES = {
    "trial": {
        "modules": {
            "dashboard": "full",
            "topseller": "full",
            "gap_analysis": "full",
            "stock_out": "full",
            "doh_analysis": "full",
            "planogram": "full",
            "replenishment": "full",
            "ai_forecasting": "full",
            "buy_plan": "full",
            "multi_channel": "full",
            "warehouse": "full",
            "data_upload": "full",
            "config": "full",
        },
        "limits": {"max_stores": 999, "max_users": 999, "data_retention_days": 7},
    },
    "starter": {
        "modules": {
            "dashboard": "full",
            "topseller": "full",
            "gap_analysis": "full",
            "stock_out": "view_only",
            "doh_analysis": "view_only",
            "planogram": "view_only",
            "replenishment": "full",
            "ai_forecasting": "none",
            "buy_plan": "none",
            "multi_channel": "none",
            "warehouse": "full",
            "data_upload": "full",
            "config": "full",
        },
        "limits": {"max_stores": 10, "max_users": 3, "data_retention_days": 30},
    },
    "professional": {
        "modules": {
            "dashboard": "full",
            "topseller": "full",
            "gap_analysis": "full",
            "stock_out": "full",
            "doh_analysis": "full",
            "planogram": "full",
            "replenishment": "full",
            "ai_forecasting": "full",
            "buy_plan": "full",
            "multi_channel": "full",
            "warehouse": "full",
            "data_upload": "full",
            "config": "full",
        },
        "limits": {"max_stores": 50, "max_users": 10, "data_retention_days": 90},
    },
    "enterprise": {
        "modules": {
            "dashboard": "full",
            "topseller": "full",
            "gap_analysis": "full",
            "stock_out": "full",
            "doh_analysis": "full",
            "planogram": "full",
            "replenishment": "full",
            "ai_forecasting": "full",
            "buy_plan": "full",
            "multi_channel": "full",
            "warehouse": "full",
            "data_upload": "full",
            "config": "full",
        },
        "limits": {"max_stores": 999999, "max_users": 999999, "data_retention_days": 999999},
    },
}


def get_module_access(plan: str, module: str) -> dict:
    cfg = PLAN_FEATURES.get(plan, PLAN_FEATURES["starter"])
    access = cfg["modules"].get(module, "none")
    return {
        "access": access,
        "can_access": access != "none",
        "view_only": access == "view_only",
        "requires_upgrade": access == "none",
    }


def get_plan_limits(plan: str) -> dict:
    return PLAN_FEATURES.get(plan, PLAN_FEATURES["starter"])["limits"]


def get_plan_info(plan: str) -> dict:
    cfg = PLAN_FEATURES.get(plan, PLAN_FEATURES["starter"])
    modules = {}
    for mod, access in cfg["modules"].items():
        modules[mod] = {
            "access": access,
            "can_access": access != "none",
            "view_only": access == "view_only",
        }
    return {"modules": modules, "limits": cfg["limits"]}
