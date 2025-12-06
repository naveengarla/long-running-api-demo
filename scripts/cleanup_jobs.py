from app.core.database import SessionLocal
from app.models.job import Job, JobStatus, JobLog
from sqlalchemy import delete

def cleanup_failed_jobs():
    db = SessionLocal()
    try:
        print("Cleaning up failed jobs...")
        # Find failed jobs
        failed_jobs_query = db.query(Job).filter(Job.status == JobStatus.FAILED.value)
        count = failed_jobs_query.count()
        
        if count == 0:
            print("No failed jobs found.")
            return

        print(f"Found {count} failed jobs. Deleting...")
        
        # We need to delete logs first if cascade isn't set up (though it is in models)
        # But let's be safe and let SQLAlchemy handle cascade if configured
        # Or just delete the jobs
        
        # Get IDs to show
        ids = [j.id for j in failed_jobs_query.all()]
        print(f"IDs to delete: {ids}")
        
        # Delete
        failed_jobs_query.delete(synchronize_session=False)
        db.commit()
        print("Cleanup complete.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_failed_jobs()
