from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from . import models, schemas
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import jwt

# Конфигурация JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Создаем таблицы, если их нет
Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service with JWT")

# Добавляем CORS middleware для разрешения запросов из других источников (например, Swagger UI API-сервиса)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # или ограничьте список, например, ["http://localhost:8000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Обновляем OAuth2PasswordBearer, чтобы tokenUrl был внешним URL, доступным из браузера
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://localhost:8001/login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user_by_login(db: Session, login: str):
    return db.query(models.User).filter(models.User.login == login).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, login: str, password: str):
    user = get_user_by_login(db, login)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Регистрация нового пользователя
@app.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if get_user_by_login(db, user.login):
        raise HTTPException(status_code=400, detail="User with this login already exists")
    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already in use")
    db_user = models.User(
        login=user.login,
        email=user.email,
        hashed_password=get_password_hash(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        date_of_birth=user.date_of_birth,
        phone=user.phone,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Логин и генерация JWT токена
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect login or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.login}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Функция для получения текущего пользователя из JWT
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("sub")
        if login is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user_by_login(db, login)
    if user is None:
        raise credentials_exception
    return user

# Получение профиля пользователя (защищенный эндпоинт)
@app.get("/profile", response_model=schemas.UserOut)
def get_profile(current_user: models.User = Depends(get_current_user)):
    return current_user

# Обновление профиля пользователя
@app.put("/profile", response_model=schemas.UserOut)
def update_profile(update: schemas.UserUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if update.first_name is not None:
        current_user.first_name = update.first_name
    if update.last_name is not None:
        current_user.last_name = update.last_name
    if update.date_of_birth is not None:
        current_user.date_of_birth = update.date_of_birth
    if update.email is not None:
        existing_user_by_email = get_user_by_email(db, update.email)
        if existing_user_by_email and existing_user_by_email.id != current_user.id:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = update.email
    if update.phone is not None:
        current_user.phone = update.phone

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)
    return current_user
