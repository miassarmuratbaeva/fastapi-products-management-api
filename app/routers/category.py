from typing import List, Annotated

from fastapi.routing import APIRouter
from fastapi import HTTPException, Path, Body, Depends, status
from sqlalchemy.orm import Session , joinedload

from ..schemas import CategoryReponse, CategoryCreate, CategoryUpdate , ProductResponse
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
