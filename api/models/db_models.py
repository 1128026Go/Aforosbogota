from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class AforoDataset(Base):
    __tablename__ = "aforo_datasets"

    id = Column(Integer, primary_key=True)
    dataset_key = Column(String(64), unique=True, nullable=False)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    frames = Column(Integer)
    tracks = Column(Integer)
    metadata_json = Column("metadata", JSON)

    accesses = relationship("AforoCardinalAccess", cascade="all, delete-orphan", back_populates="dataset")
    rilsa_rules = relationship("AforoRilsaRule", cascade="all, delete-orphan", back_populates="dataset")
    events = relationship("AforoTrajectoryEvent", cascade="all, delete-orphan", back_populates="dataset")
    movement_counts = relationship("AforoMovementCount", cascade="all, delete-orphan", back_populates="dataset")
    history_entries = relationship("AforoDatasetHistory", cascade="all, delete-orphan", back_populates="dataset")


class AforoCardinalAccess(Base):
    __tablename__ = "aforo_cardinal_accesses"

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("aforo_datasets.id", ondelete="CASCADE"), nullable=False)
    access_id = Column(String(128), nullable=False)
    display_name = Column(String(255))
    cardinal = Column(String(8), nullable=False)
    cardinal_official = Column(String(8), nullable=False)
    x = Column(Numeric)
    y = Column(Numeric)
    gate = Column(JSON)
    polygon = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset = relationship("AforoDataset", back_populates="accesses")

    __table_args__ = (UniqueConstraint("dataset_id", "access_id", name="uq_access_dataset"),)


class AforoRilsaRule(Base):
    __tablename__ = "aforo_rilsa_rules"

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("aforo_datasets.id", ondelete="CASCADE"), nullable=False)
    origin_access = Column(String(128), nullable=False)
    dest_access = Column(String(128), nullable=False)
    rilsa_code = Column(Integer, nullable=False)
    metadata_json = Column("metadata", JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset = relationship("AforoDataset", back_populates="rilsa_rules")

    __table_args__ = (
        UniqueConstraint("dataset_id", "origin_access", "dest_access", name="uq_rilsa_rule"),
    )


class AforoTrajectoryEvent(Base):
    __tablename__ = "aforo_trajectory_events"

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("aforo_datasets.id", ondelete="CASCADE"), nullable=False)
    track_id = Column(String(128), nullable=False)
    class_name = Column("class", String(64))
    origin_access = Column(String(128))
    dest_access = Column(String(128))
    origin_cardinal = Column(String(8))
    destination_cardinal = Column(String(8))
    mov_rilsa = Column(Integer)
    frame_entry = Column(Integer)
    frame_exit = Column(Integer)
    timestamp_entry = Column(DateTime)
    timestamp_exit = Column(DateTime)
    confidence = Column(Numeric)
    hide_in_pdf = Column(Boolean, default=False)
    discarded = Column(Boolean, default=False)
    positions = Column(JSON)
    extra = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset = relationship("AforoDataset", back_populates="events")
    revisions = relationship("AforoTrajectoryEventRevision", cascade="all, delete-orphan", back_populates="event")

    __table_args__ = (UniqueConstraint("dataset_id", "track_id", name="uq_event_track"),)


class AforoTrajectoryEventRevision(Base):
    __tablename__ = "aforo_trajectory_event_revisions"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("aforo_trajectory_events.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False)
    changes = Column(JSON, nullable=False)
    changed_by = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("AforoTrajectoryEvent", back_populates="revisions")

    __table_args__ = (UniqueConstraint("event_id", "version", name="uq_event_version"),)


class AforoMovementCount(Base):
    __tablename__ = "aforo_movement_counts"

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("aforo_datasets.id", ondelete="CASCADE"), nullable=False)
    movement_code = Column(Integer, nullable=False)
    interval_start = Column(DateTime, nullable=False)
    interval_end = Column(DateTime, nullable=False)
    totals = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset = relationship("AforoDataset", back_populates="movement_counts")

    __table_args__ = (
        UniqueConstraint("dataset_id", "movement_code", "interval_start", name="uq_movement_interval"),
    )


class AforoDatasetHistory(Base):
    __tablename__ = "aforo_dataset_history"

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("aforo_datasets.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(128), nullable=False)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    dataset = relationship("AforoDataset", back_populates="history_entries")
