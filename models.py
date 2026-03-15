import enum
from sqlalchemy import Column, Integer, String, Date, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class EquipmentStatus(str, enum.Enum):
    active = "active"
    under_repair = "under_repair"
    retired = "retired"

class MaintenanceStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    missed = "missed"

class RepairStatus(str, enum.Enum):
    reported = "reported"
    in_progress = "in_progress"
    resolved = "resolved"

class UserRole(str, enum.Enum):
    admin = "admin"
    technician = "technician"

class NotificationType(str, enum.Enum):
    upcoming_maintenance = "upcoming_maintenance"
    overdue_maintenance = "overdue_maintenance"
    repair_update = "repair_update"
    new_repair = "new_repair"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    phone_number = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.technician)
    email_alerts_enabled = Column(Integer, default=1) # Boolean
    whatsapp_alerts_enabled = Column(Integer, default=1) # Boolean
    password_hash = Column(String, nullable=True) # For now, allow null for existing users
    is_active = Column(Integer, default=1) # Boolean

    notifications = relationship("Notification", back_populates="user")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    message = Column(Text)
    type = Column(Enum(NotificationType))
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=True)
    reference_id = Column(Integer, nullable=True)
    is_read = Column(Integer, default=0) # Boolean
    created_at = Column(Date, default=datetime.date.today)

    user = relationship("User", back_populates="notifications")
    equipment = relationship("Equipment")

class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    asset_id = Column(String, unique=True, index=True)
    serial_number = Column(String, unique=True, index=True)
    manufacturer = Column(String)
    model = Column(String)
    department = Column(String)
    purchase_date = Column(Date)
    warranty_expiry = Column(Date, nullable=True)
    status = Column(Enum(EquipmentStatus), default=EquipmentStatus.active)
    maintenance_frequency_days = Column(Integer)
    next_maintenance_date = Column(Date)
    
    maintenance_records = relationship("MaintenanceRecord", back_populates="equipment")
    repair_records = relationship("RepairRecord", back_populates="equipment")

class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    maintenance_date = Column(Date)
    performed_by = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    status = Column(Enum(MaintenanceStatus), default=MaintenanceStatus.scheduled)
    cost = Column(Integer, nullable=True) # Adding as Integer/Float for tracking

    equipment = relationship("Equipment", back_populates="maintenance_records")

class RepairRecord(Base):
    __tablename__ = "repair_records"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"))
    issue_description = Column(Text)
    repair_date = Column(Date)
    technician_notes = Column(Text, nullable=True)
    status = Column(Enum(RepairStatus), default=RepairStatus.reported)
    cost = Column(Integer, nullable=True)

    equipment = relationship("Equipment", back_populates="repair_records")
