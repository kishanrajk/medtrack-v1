from pydantic import BaseModel, Field
from datetime import date
from typing import Optional, List
from models import EquipmentStatus, MaintenanceStatus, RepairStatus, UserRole, NotificationType

# --- Equipment Schemas ---
class EquipmentBase(BaseModel):
    name: str
    asset_id: str
    serial_number: str
    manufacturer: str
    model: str
    department: str
    purchase_date: date
    warranty_expiry: Optional[date] = None
    status: EquipmentStatus = EquipmentStatus.active
    maintenance_frequency_days: int

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    asset_id: Optional[str] = None
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    department: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_expiry: Optional[date] = None
    status: Optional[EquipmentStatus] = None
    maintenance_frequency_days: Optional[int] = None
    next_maintenance_date: Optional[date] = None

class EquipmentOut(EquipmentBase):
    id: int
    next_maintenance_date: date

    class Config:
        from_attributes = True

# --- Maintenance Schemas ---
class MaintenanceBase(BaseModel):
    maintenance_date: date
    performed_by: Optional[str] = None
    notes: Optional[str] = None
    status: MaintenanceStatus = MaintenanceStatus.scheduled
    cost: Optional[float] = None

class MaintenanceCreate(MaintenanceBase):
    pass

class MaintenanceUpdate(BaseModel):
    status: MaintenanceStatus
    performed_by: Optional[str] = None
    notes: Optional[str] = None
    cost: Optional[float] = None

class MaintenanceOut(MaintenanceBase):
    id: int
    equipment_id: int

    class Config:
        from_attributes = True

# --- Repair Schemas ---
class RepairBase(BaseModel):
    issue_description: str
    repair_date: date
    technician_notes: Optional[str] = None
    status: RepairStatus = RepairStatus.reported
    cost: Optional[float] = None

class RepairCreate(RepairBase):
    pass

class RepairUpdate(BaseModel):
    status: Optional[RepairStatus] = None
    technician_notes: Optional[str] = None
    cost: Optional[float] = None

class RepairOut(RepairBase):
    id: int
    equipment_id: int

    class Config:
        from_attributes = True

# --- Aggregated Schemas ---
class EquipmentDetail(EquipmentOut):
    maintenance_records: List[MaintenanceOut] = []
    repair_records: List[RepairOut] = []

# --- Users ---
class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    phone_number: Optional[str] = None
    role: str
    email_alerts_enabled: int
    whatsapp_alerts_enabled: int
    is_active: int
    
    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    name: str
    email: str
    phone_number: Optional[str] = None
    password: str
    role: UserRole = UserRole.technician
    email_alerts_enabled: int = 1
    whatsapp_alerts_enabled: int = 1

# --- Notifications ---
class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    equipment_id: Optional[int] = None
    reference_id: Optional[int] = None
    is_read: int
    created_at: date
    
    class Config:
        from_attributes = True
# --- Stats ---
class CostStats(BaseModel):
    labels: List[str]
    maintenanceCosts: List[float]
    repairCosts: List[float]
