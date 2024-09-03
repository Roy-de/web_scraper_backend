from typing import Optional


class Result:
    def __init__(self, price: Optional[str] = None, status: Optional[str] = None, category: Optional[str] = None):
        self.price = price
        self.status = status
        self.category = category

    def to_dict(self):
        return {
            'price': self.price,
            'status': self.status,
            'category': self.category
        }
