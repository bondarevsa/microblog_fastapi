from datetime import datetime
from app.auth.database import Base
from sqlalchemy.orm import relationship
from app.auth.database import User
from sqlalchemy import MetaData, Integer, String, TIMESTAMP, Column, Table, Boolean, DateTime, ForeignKey

metadata = MetaData()

user = Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, nullable=False),
    Column("username", String, nullable=False),
    Column("registered_at", TIMESTAMP, default=datetime.utcnow),
    Column("hashed_password", String, nullable=False),
    Column("is_active", Boolean, default=True, nullable=False),
    Column("is_superuser", Boolean, default=False, nullable=False),
    Column("is_verified", Boolean, default=False, nullable=False),
)



