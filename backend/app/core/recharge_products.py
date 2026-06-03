"""
充值档位配置
定义所有可购买的积分套餐，前端通过 API 获取此列表
"""

RECHARGE_PRODUCTS = [
    {
        "id": 1,
        "name": "体验包",
        "amount": 6,
        "credits": 6000,
        "bonus": 0,
        "total_credits": 6000,
        "sort": 1,
    },
    {
        "id": 2,
        "name": "标准包",
        "amount": 30,
        "credits": 30000,
        "bonus": 3000,
        "total_credits": 33000,
        "sort": 2,
    },
    {
        "id": 3,
        "name": "进阶包",
        "amount": 98,
        "credits": 98000,
        "bonus": 20000,
        "total_credits": 118000,
        "sort": 3,
    },
    {
        "id": 4,
        "name": "豪华包",
        "amount": 298,
        "credits": 298000,
        "bonus": 100000,
        "total_credits": 398000,
        "sort": 4,
    },
]


def get_product_by_id(product_id: int) -> dict | None:
    """根据 ID 查找档位，找不到返回 None"""
    for p in RECHARGE_PRODUCTS:
        if p["id"] == product_id:
            return p
    return None
