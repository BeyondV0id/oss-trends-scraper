from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    UniqueConstraint,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Repo(Base):
    __tablename__ = "repos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    github_id = Column(Integer, nullable=True, unique=True)
    owner = Column(String(256), nullable=False)
    repo_name = Column(String(256), nullable=False)
    full_name = Column(String(256), nullable=False, unique=True, index=True)
    url = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(String(100), nullable=True)
    stargazers_count = Column(Integer, nullable=False, default=0)
    forks_count = Column(Integer, nullable=False, default=0)
    watchers_count = Column(Integer, nullable=False, default=0)
    open_issues_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    last_synced_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    trending = relationship("TrendingRepo", back_populates="repo", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Repo {self.full_name}>"


class TrendingRepo(Base):
    __tablename__ = "trending_repos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False)
    period = Column(String(50), nullable=False)  # 'daily', 'weekly', 'monthly'
    stars_earned = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=True, default=datetime.utcnow)

    repo = relationship("Repo", back_populates="trending")

    __table_args__ = (
        UniqueConstraint("repo_id", "period", name="repo_period_idx"),
        Index("idx_trending_period", "period"),
    )

    def __repr__(self):
        return f"<TrendingRepo repo_id={self.repo_id} period={self.period}>"
