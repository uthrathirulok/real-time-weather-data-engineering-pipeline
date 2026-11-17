
from apscheduler.schedulers.blocking import BlockingScheduler

from main import main


def start_scheduler():
    """
    Run the weather ETL pipeline automatically every 15 minutes.
    """

    scheduler = BlockingScheduler()

    # Run the pipeline every 15 minutes
    scheduler.add_job(
        main,
        trigger="interval",
        minutes=15,
        id="weather_pipeline_job",
        name="Weather Data ETL Pipeline",
        max_instances=1,
        coalesce=True
    )

    print("=" * 55)
    print("WEATHER PIPELINE SCHEDULER")
    print("=" * 55)
    print("Pipeline will run automatically every 15 minutes.")
    print("Press CTRL + C to stop the scheduler.")
    print("=" * 55)

    try:
        scheduler.start()

    except (KeyboardInterrupt, SystemExit):
        print("\nWeather pipeline scheduler stopped.")


if __name__ == "__main__":
    start_scheduler()
