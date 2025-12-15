from typing import List, Annotated

from fastapi.routing import APIRouter
from fastapi import HTTPException, Path, Body, Depends, status, Query
from sqlalchemy.orm import Session , joinedload
from sqlalchemy import asc, desc, func

from ..schemas import (
    CategoryReponse, CategoryCreate, 
    CategoryUpdate , ProductResponse,
    ProductUpdateRequest, PaginatedProductsResponse, 
    ProductsCountResponse, ProductSummary,
    ProductsStatisticsResponse
    )
from ..database import get_db
from ..models import Category
from ..models import Product

router = APIRouter(
    prefix=["\products"],
    tags=['Categories']
)


@router.get('/', response_model=List[CategoryReponse])
def get_categories(
    session: Annotated[Session, Depends(get_db)],
):
    return session.query(Category).all() 


@router.get('/{category_id}', response_model=CategoryReponse)
def get_one_category(
    category_id: Annotated[int, Path(ge=1)],
    session: Annotated[Session, Depends(get_db)],
):
    category = session.query(Category).get(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail='Category not found.'
        )
    
    return category


@router.post('/', response_model=CategoryReponse, status_code=status.HTTP_201_CREATED)
def create_category(
    data: CategoryCreate,
    session: Annotated[Session, Depends(get_db)],
):
    existing_category = session.query(Category).filter(Category.name==data.name).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Category with this name already exists"
        )

    new_category = Category(name=data.name, description=data.description)
    session.add(new_category)
    session.commit()
    session.refresh(new_category)

    return new_category


@router.put('/{category_id}', response_model=CategoryReponse, status_code=status.HTTP_204_NO_CONTENT)
def update_category(
    category_id: Annotated[int, Path(ge=1)],
    data: Annotated[CategoryUpdate, Body],
    session: Session = Depends(get_db)
):
    existing_category = session.query(Category).get(category_id)

    if not existing_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Category not found')

    if session.query(Category).filter(Category.name==data.name).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Category with name \'Electronics\' already exists')

    existing_category.name = data.name if data.name else existing_category.name
    existing_category.description = data.description if data.description else existing_category.description

    session.commit()
    session.refresh(existing_category)

    return existing_category


@router.delete('/{category_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: Annotated[int, Path(ge=1)],
    session: Annotated[Session, Depends(get_db)],
):
    existing_category = session.query(Category).get(category_id)

    if not existing_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Category not found')

    products = existing_category.products.count()
    if products > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f'Cannot delete category. {products} products are linked to this category')
    
    session.delete(existing_category)
    session.commit()

    return {
        "message": "Category deleted successfully"
    }
    


@router.get('/{category_id}',  response_model=List[CategoryReponse])
def get_all_products(
    session: Annotated[Session, Depends(get_db)]
):
    products = (session.query(Product).options(joinedload(Product.category)).all())
    return products


@router.get("/{product_id}", response_model=ProductResponse,status_code=status.HTTP_200_OK)
def get_product_by_id(
    product_id: Annotated[int, Path(ge=1)],
    session: Annotated[Session, Depends(get_db)]
):
    product = ( session.query(Product) .options(joinedload(Product.category))
        .filter(Product.id == product_id).first())

    if not product:
        raise HTTPException( status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found")

    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    updates: ProductUpdateRequest,
    session: Annotated[Session, Depends(get_db)]
):
    product = session.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    update_data = updates.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    session.commit()
    session.refresh(product)
    return product



@router.delete("/{product_id}")
def delete_product( product_id: int, session: Annotated[Session, Depends(get_db)]):
    
    product = session.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    session.delete(product)
    session.commit()
    return {"message": "Product o'chirildi"}


@router.get("/search", response_model=List[ProductResponse])
def search_products(name: Annotated[str | None, Query(min_length=1)] = None,
    session: Annotated[Session, Depends(get_db)] = Depends(get_db)):

    query = session.query(Product)

    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))

    results = query.all()
    return results



@router.get("/filter/category", response_model=List[ProductResponse])
def filter_products_by_category(category: Annotated[str, Query(..., min_length=2)],
    session: Annotated[Session, Depends(get_db)] = Depends(get_db)):
    
    results = session.query(Product).join(Product.category).filter(Product.category.has(name=category)).all()
    
    return results


@router.get("/filter/price", response_model=List[ProductResponse])
def filter_products_by_price(
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    session: Annotated[Session, Depends(get_db)] = Depends(get_db)
):
   
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be greater than max_price"
        )
    
    query = session.query(Product)

    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    results = query.all()
    return results


@router.get("/filter/stock", response_model=List[ProductResponse])
def filter_products_by_stock(
    in_stock: Annotated[bool, Query(...)],
    session: Annotated[Session, Depends(get_db)] = Depends(get_db)):
    results = session.query(Product).filter(Product.in_stock == in_stock).all()
    return results



@router.get("/paginated", response_model=PaginatedProductsResponse)
def get_products_paginated(
    limit: Annotated[int, Query(10, ge=1, le=100)] = 10,
    offset: Annotated[int, Query(0, ge=0)] = 0,
    session: Annotated[Session, Depends(get_db)] = Depends(get_db)):
   
    total = session.query(Product).count()
    items = session.query(Product).offset(offset).limit(limit).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items
    }



@router.get("/category/{category_id}", response_model=List[ProductResponse])
def get_products_by_category_id(
    category_id: Annotated[int, Path(..., gt=0)],
    session: Annotated[Session, Depends(get_db)] = Depends(get_db)):
    category = session.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    
    products = session.query(Product).filter(Product.category_id == category_id).all()
    return products

@router.get("/sort/price", response_model=List[ProductResponse])
def sort_products_by_price(
    order: Annotated[str, Query(..., regex="^(asc|desc)$")],
    session: Annotated[Session, Depends(get_db)] = Depends(get_db)
):
    
    if order == "asc":
        products = session.query(Product).order_by(asc(Product.price)).all()
    else:  
        products = session.query(Product).order_by(desc(Product.price)).all()
    
    return products


@router.get("/advanced-search", response_model=PaginatedProductsResponse)
def advanced_search_products(
    name: Annotated[str | None, Query(min_length=1)] = None,
    category_id: Annotated[int | None, Query(gt=0)] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
    in_stock: Annotated[bool | None, Query()] = None,
    sort_by: Annotated[str | None, Query(regex="^(price_asc|price_desc|name_asc|name_desc)$")] = None,
    limit: Annotated[int, Query(20, ge=1, le=100)] = 20,
    offset: Annotated[int, Query(0, ge=0)] = 0,
    session: Annotated[Session, Depends(get_db)] = Depends(get_db)
):
    

    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be greater than max_price"
        )

    if category_id is not None:
        category = session.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
            )

    query = session.query(Product)

    if name:
        query = query.filter(Product.name.ilike(f"%{name}%"))
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if in_stock is not None:
        query = query.filter(Product.in_stock == in_stock)

    total = query.count()

    if sort_by:
        if sort_by == "price_asc":
            query = query.order_by(asc(Product.price))
        elif sort_by == "price_desc":
            query = query.order_by(desc(Product.price))
        elif sort_by == "name_asc":
            query = query.order_by(asc(Product.name))
        elif sort_by == "name_desc":
            query = query.order_by(desc(Product.name))

    items = query.offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items
    }



@router.get("/count", response_model=ProductsCountResponse)
def get_products_count(
    category_id: Annotated[int | None, Query(gt=0)] = None,
    in_stock: Annotated[bool | None, Query()] = None,
    session: Annotated[Session, Depends(get_db)] = Depends(get_db)
):
    
    query = session.query(Product)

    if category_id is not None:
        category = session.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Category with id {category_id} not found"
            )
        query = query.filter(Product.category_id == category_id)

    if in_stock is not None:
        query = query.filter(Product.in_stock == in_stock)

    total = query.count()
    in_stock_count = query.filter(Product.in_stock == True).count()
    out_of_stock_count = total - in_stock_count

    return {
        "total": total,
        "in_stock": in_stock_count,
        "out_of_stock": out_of_stock_count
    }


@router.get("/statistics", response_model=ProductsStatisticsResponse)
def get_products_statistics(session: Session = Depends(get_db)):
  
    total_products = session.query(func.count(Product.id)).scalar()
    total_categories = session.query(func.count(Category.id)).scalar()
    in_stock_count = session.query(func.count(Product.id)).filter(Product.in_stock == True).scalar()
    out_of_stock_count = total_products - in_stock_count if total_products else 0
    average_price = session.query(func.avg(Product.price)).scalar()
    min_price = session.query(func.min(Product.price)).scalar()
    max_price = session.query(func.max(Product.price)).scalar()

    most_expensive = session.query(Product).order_by(desc(Product.price)).first()
    cheapest = session.query(Product).order_by(asc(Product.price)).first()

    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "average_price": float(average_price) if average_price is not None else None,
        "min_price": float(min_price) if min_price is not None else None,
        "max_price": float(max_price) if max_price is not None else None,
        "most_expensive_product": {
            "id": most_expensive.id,
            "name": most_expensive.name,
            "price": most_expensive.price
        } if most_expensive else None,
        "cheapest_product": {
            "id": cheapest.id,
            "name": cheapest.name,
            "price": cheapest.price
        } if cheapest else None
    }