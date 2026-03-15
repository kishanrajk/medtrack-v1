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
    today = date.today()
    
    # Calculate month buckets (Last 5 months + current)
    months = []
    for i in range(5, -1, -1):
        m = today.month - i
        y = today.year
        while m <= 0:
            m += 12
            y -= 1
        months.append(f"{y}-{m:02d}")
    
    # Fetch records (use a wide window)
    six_months_ago = today - timedelta(days=200)
    
    maint_records = db.query(models.MaintenanceRecord).filter(
        models.MaintenanceRecord.maintenance_date >= six_months_ago,
        models.MaintenanceRecord.status == models.MaintenanceStatus.completed
    ).all()
    
    repair_records = db.query(models.RepairRecord).filter(
        models.RepairRecord.repair_date >= six_months_ago,
        models.RepairRecord.status == models.RepairStatus.resolved
    ).all()
    
    # Aggregate in Python with explicit keys
    maint_map = defaultdict(float)
    for r in maint_records:
        if r.maintenance_date and r.cost:
            m_key = f"{r.maintenance_date.year}-{r.maintenance_date.month:02d}"
            maint_map[m_key] += float(r.cost)
            
    repair_map = defaultdict(float)
    for r in repair_records:
        if r.repair_date and r.cost:
            r_key = f"{r.repair_date.year}-{r.repair_date.month:02d}"
            repair_map[r_key] += float(r.cost)
            
    maint_data = [maint_map[m] for m in months]
    repair_data = [repair_map[m] for m in months]
    
    # Debug: Print to server logs
    print(f"DEBUG: Buckets={months}")
    print(f"DEBUG: MaintData={maint_data}")
    print(f"DEBUG: RepairData={repair_data}")
    
    # Convert labels to "Jan 25"
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
