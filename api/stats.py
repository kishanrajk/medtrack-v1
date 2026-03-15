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
    six_months_ago = today - timedelta(days=180)
    
    # 1. Fetch Maintenance Costs
    maint_records = db.query(
        func.strftime('%Y-%m', models.MaintenanceRecord.maintenance_date).label('month'),
        func.sum(models.MaintenanceRecord.cost).label('total')
    ).filter(
        models.MaintenanceRecord.maintenance_date >= six_months_ago,
        models.MaintenanceRecord.status == models.MaintenanceStatus.completed
    ).group_by('month').all()
    
    # 2. Fetch Repair Costs
    repair_records = db.query(
        func.strftime('%Y-%m', models.RepairRecord.repair_date).label('month'),
        func.sum(models.RepairRecord.cost).label('total')
    ).filter(
        models.RepairRecord.repair_date >= six_months_ago,
        models.RepairRecord.status == models.RepairStatus.resolved
    ).group_by('month').all()
    
    # Process data into a format Chart.js likes
    # Labels for the last 6 months
    months = []
    for i in range(5, -1, -1):
        d = today - timedelta(days=i*30)
        months.append(d.strftime('%Y-%m'))
    
    maint_map = {m: c for m, c in maint_records}
    repair_map = {m: c for m, c in repair_records}
    
    maint_data = [float(maint_map.get(m, 0) or 0) for m in months]
    repair_data = [float(repair_map.get(m, 0) or 0) for m in months]
    
    # Convert labels to more readable format like "Jan", "Feb"
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
        return {"status": "success", "message": "Database seeded manually!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
