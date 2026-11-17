
import logging
from apscheduler.schedulers.blocking import BlockingScheduler

from main import main


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def run_pipeline():
    """Execute the weather data pipeline."""

    try:
        logger.info("Starting scheduled weather pipeline...")
        main()
        logger.info("Scheduled pipeline execution completed.")

    except Exception:
        logger.exception("Scheduled pipeline execution failed.")


if __name__ == "__main__":

    # Set up scheduler using Indian Standard Time
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    # Run the pipeline immediately when scheduler starts
    run_pipeline()

    # Schedule automatic execution every 15 minutes
    scheduler.add_job(
        run_pipeline,
        trigger="interval",
        minutes=15,
        id="weather_pipeline_job",
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
        replace_existing=True
    )

    print("\n" + "=" * 50)
    print("WEATHER PIPELINE SCHEDULER STARTED")
    print("=" * 50)
    print("First pipeline execution: Completed / In progress")
    print("Next executions: Every 15 minutes")
    print("Timezone: Asia/Kolkata")
    print("Press CTRL + C to stop the scheduler.")
    print("=" * 50 + "\n")

    try:
        scheduler.start()

    except (KeyboardInterrupt, SystemExit):
        print("\nWeather pipeline scheduler stopped.")
        logger.info("Scheduler stopped.")
