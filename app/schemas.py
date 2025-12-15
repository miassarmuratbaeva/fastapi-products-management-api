from typing import List, Annotated, Optional

from pydantic import BaseModel, Field, constr, condecimal


class ProductResponse(BaseModel):
    product_id: int
    name: Annotated[str, Field(max_length=100)]
    price: float
    in_stock: bool

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    category_id: int
    name: Annotated[str, Field(max_length=100)]
    price: float
    in_stock: Annotated[bool, Field(True)]


class CategoryReponse(BaseModel):
    category_id: int
    name: Annotated[str, Field(max_length=100)]
    description: str | None = None
    products: Annotated[List[ProductResponse], []]

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=100)]
    description: Annotated[str, Field(None, max_length=500)]


class CategoryUpdate(BaseModel):
    name: Annotated[str, Field(None, min_length=2, max_length=100)]
    description: Annotated[str, Field(None, max_length=500)]


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None
    category_id: Optional[int] = None


class PaginatedProductsResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[ProductResponse]



class ProductsCountResponse(BaseModel):
    total: int
    in_stock: int
    out_of_stock: int


class ProductSummary(BaseModel):
    id: int
    name: str
    price: float


class ProductsStatisticsResponse(BaseModel):
    total_products: int
    total_categories: int
    in_stock_count: int
    out_of_stock_count: int
    average_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    most_expensive_product: Optional[ProductSummary]
    cheapest_product: Optional[ProductSummary]
