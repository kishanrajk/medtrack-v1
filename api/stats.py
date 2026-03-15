from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
import models, schemas
from database import get_db
from collections import defaultdict

router = APIRouter()

@router.get("/costs", response_model=schemas.CostStats)
def get_cost_stats(db: Session = Depends(get_db)):
    # Get costs for the last 6 months
    today = date.today()
    
    # Calculate month buckets (Last 5 months + current)
    months = []
    for i in range(5, -1, -1):
        # Handle month/year wrap-around
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        months.append(f"{y}-{m:02d}")
    
    # Fetch records
    six_months_ago = today - timedelta(days=185) # Buffer
    
    maint_records = db.query(models.MaintenanceRecord).filter(
        models.MaintenanceRecord.maintenance_date >= six_months_ago,
        models.MaintenanceRecord.status == models.MaintenanceStatus.completed
    ).all()
    
    repair_records = db.query(models.RepairRecord).filter(
        models.RepairRecord.repair_date >= six_months_ago,
        models.RepairRecord.status == models.RepairStatus.resolved
    ).all()
    
    # Aggregate in Python
    maint_map = defaultdict(float)
    for r in maint_records:
        if r.maintenance_date:
            m_key = r.maintenance_date.strftime('%Y-%m')
            maint_map[m_key] += float(r.cost or 0)
            
    repair_map = defaultdict(float)
    for r in repair_records:
        if r.repair_date:
            r_key = r.repair_date.strftime('%Y-%m')
            repair_map[r_key] += float(r.cost or 0)
            
    maint_data = [maint_map[m] for m in months]
    repair_data = [repair_map[m] for m in months]
    
    # Convert labels to more readable format like "Jan 25"
    month_names = []
    for m in months:
        y, mon = m.split('-')
        month_names.append(date(int(y), int(mon), 1).strftime('%b %y'))
        
    return {
        "labels": month_names,
        "maintenanceCosts": maint_data,
        "repairCosts": repair_data
    }

@router.get("/seed")
def manual_seed():
    from seed_data import seed_db
    try:
        seed_db()
        return {
            "status": "success", 
            "message": "Database seeded manually!",
            "version": "v1.2-no-args-fixed"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "debug_info": "seed_db signature verified locally"
        }
