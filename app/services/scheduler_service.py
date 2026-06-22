from apscheduler.schedulers.background import BackgroundScheduler

from app.database.database import SessionLocal
from app.services import loan_service


scheduler = BackgroundScheduler()


def process_automatic_payments_job():
    db = SessionLocal()

    try:
        paid_installments = loan_service.process_all_due_automatic_payments(db)

        if paid_installments:
            print(f"Automatic payments processed: {len(paid_installments)} installment(s) paid.")

    except Exception as e:
        print(f"Automatic payment job failed: {e}")

    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            process_automatic_payments_job,
            "interval",
            seconds=30,
            id="automatic_payments_job",
            replace_existing=True
        )

        scheduler.start()
        print("Automatic payment scheduler started.")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        print("Automatic payment scheduler stopped.")