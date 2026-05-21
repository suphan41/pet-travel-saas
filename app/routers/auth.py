from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, Tenant
from app.auth import hash_password, verify_password, create_access_token
import uuid

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register")
def register(
    email: str,
    password: str,
    name: str,
    db: Session = Depends(get_db)
):
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    tenant = db.query(Tenant).first()

    if not tenant:
        tenant = Tenant(
            id=uuid.uuid4(),
            name="Default Tenant",
            domain="default"
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)

    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant.id,
        email=email,
        name=name,
        hashed_password=hash_password(password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User registered successfully"}


@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "sub": str(user.id),
        "tenant_id": str(user.tenant_id),
        "role": user.role
    })

    return {
        "access_token": token,
        "name": user.name,
        "email": user.email,
        "id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "token_type": "bearer"
    }