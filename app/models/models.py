from datetime import datetime
from app.auth.database import Base
from sqlalchemy.orm import relationship
from app.auth.database import User
from sqlalchemy import MetaData, Integer, String, TIMESTAMP, Column, Table, Boolean, DateTime, ForeignKey, ARRAY

metadata = MetaData()

user = Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, nullable=False),
    Column("username", String, nullable=False),
    Column("registered_at", TIMESTAMP, default=datetime.utcnow),
    Column("about_me", String),
    Column("last_seen", TIMESTAMP, default=datetime.utcnow),
    Column("followers", ARRAY(Integer), default=[]),
    Column("following", ARRAY(Integer), default=[]),
    Column("hashed_password", String, nullable=False),
    Column("is_active", Boolean, default=True, nullable=False),
    Column("is_superuser", Boolean, default=False, nullable=False),
    Column("is_verified", Boolean, default=False, nullable=False),
)

post = Table(
    "post",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("body", String),
    Column("header", String),
    Column("timestamp", TIMESTAMP, default=datetime.utcnow),
    Column("user_id", Integer, ForeignKey("user.id"))
)

comment = Table(
    "comment",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("text", String),
    Column("created_at", TIMESTAMP, default=datetime.utcnow),
    Column("user_id", Integer, ForeignKey("user.id")),
    Column("post_id", Integer, ForeignKey("post.id"))
)
