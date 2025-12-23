from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date, timedelta
from sqlalchemy.orm import Session
from backend.models.database import SessionLocal
from backend.models.models import Tenant, Alert
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def check_expiring_agreements():
    """Check for tenants with agreements expiring within 30 days"""
    db: Session = SessionLocal()
    try:
        today = date.today()
        expiry_date = today + timedelta(days=30)
        
        # Find tenants with expiring agreements
        expiring_tenants = db.query(Tenant).filter(
            Tenant.agreement_end_date >= today,
            Tenant.agreement_end_date <= expiry_date
        ).all()
        
        logger.info(f"Found {len(expiring_tenants)} tenants with expiring agreements")
        
        for tenant in expiring_tenants:
            days_remaining = (tenant.agreement_end_date - today).days
            
            # Check if alert already exists
            existing_alert = db.query(Alert).filter(
                Alert.tenant_id == tenant.tenant_id,
                Alert.is_read == False
            ).first()
            
            if not existing_alert:
                # Create new alert
                alert = Alert(
                    tenant_id=tenant.tenant_id,
                    tenant_name=tenant.name,
                    building_name=tenant.building.building_name if tenant.building else "N/A",
                    agreement_end_date=tenant.agreement_end_date,
                    days_remaining=days_remaining,
                    is_read=False
                )
                db.add(alert)
                logger.info(f"Created alert for tenant {tenant.name} - {days_remaining} days remaining")
            else:
                # Update existing alert
                existing_alert.days_remaining = days_remaining
                existing_alert.agreement_end_date = tenant.agreement_end_date
                logger.info(f"Updated alert for tenant {tenant.name} - {days_remaining} days remaining")
        
        # Mark alerts as read for tenants whose agreements have expired
        expired_alerts = db.query(Alert).join(Tenant).filter(
            Tenant.agreement_end_date < today,
            Alert.is_read == False
        ).all()
        
        for alert in expired_alerts:
            alert.is_read = True
            logger.info(f"Marked alert as read for expired tenant {alert.tenant_name}")
        
        db.commit()
        
    except Exception as e:
        logger.error(f"Error checking expiring agreements: {str(e)}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler"""
    if not scheduler.running:
        # Schedule job to run daily at 9:00 AM
        scheduler.add_job(
            check_expiring_agreements,
            trigger=CronTrigger(hour=9, minute=0),
            id='check_expiring_agreements',
            name='Check for expiring agreements',
            replace_existing=True
        )
        scheduler.start()
        logger.info("Scheduler started - checking for expiring agreements daily at 9:00 AM")
        
        # Run immediately on startup
        check_expiring_agreements()


def stop_scheduler():
    """Stop the background scheduler"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")

