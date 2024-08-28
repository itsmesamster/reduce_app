# standard
from time import sleep
from datetime import datetime
from math import ceil
import threading
import multiprocessing


# 3rd party
import schedule
from click import Command


# project
from app.core.custom_logger import logger


def scheduler(fn: callable, fn_kwargs: dict = None, schedule_times: list[str] = None):
    if schedule_times:
        logger.info(f"Daily scheduled times: {schedule_times}.")
    else:
        logger.warning("No HH:MM times specified for scheduler. Will run every hour.")
        schedule_times = [f"{hour:02d}:00" for hour in range(24)]

    for schedule_time in schedule_times:
        schedule.every().day.at(schedule_time).do(fn, fn_kwargs)
    try:
        logger.info(f"Starting scheduler... for {fn.__name__}")
    except AttributeError:
        if isinstance(fn, Command):
            logger.info(f"Starting scheduler... for {fn.name}")
        else:
            logger.error("Error when starting scheduler.")

    while True:
        logger.info(f'Time now: {datetime.now().astimezone().strftime("%H:%M %Z")}')
        schedule.run_pending()
        next_run = schedule.next_run()
        logger.info(f"Scheduler next run @ about {next_run}.")
        next_run_in_seconds = int((next_run - datetime.now()).seconds)
        next_run_in_minutes = ceil(next_run_in_seconds / 60)
        logger.info(f"Sleeping for {next_run_in_minutes} minutes.")
        if next_run_in_seconds < 5:
            next_run_in_seconds = 5
        sleep(next_run_in_seconds)


def scheduler_thread(
    fn: callable, fn_kwargs: dict = None, schedule_times: list[str] = None
):
    try_restart_minutes = 20
    try:
        threading.Thread(
            target=scheduler,
            kwargs={"fn": fn, "fn_kwargs": fn_kwargs, "schedule_times": schedule_times},
        ).start()
    except Exception as e:
        logger.error(f"Error in scheduler thread: {e}")
        logger.info(
            f"FALLBACK: Trying to start the scheduler again "
            f"for {fn.__name__} in {try_restart_minutes} minutes..."
        )
        sleep(try_restart_minutes * 60)
        scheduler_thread(fn, fn_kwargs, schedule_times)


def scheduler_process(
    fn: callable, fn_kwargs: dict = None, schedule_times: list[str] = None
):
    try_restart_minutes = 20
    try:
        multiprocessing.Process(
            target=scheduler,
            kwargs={"fn": fn, "fn_kwargs": fn_kwargs, "schedule_times": schedule_times},
        ).start()
    except Exception as e:
        logger.error(f"Error in scheduler process: {e}")
        logger.info(
            f"FALLBACK: Trying to start the scheduler again "
            f"for {fn.__name__} in {try_restart_minutes} minutes..."
        )
        sleep(try_restart_minutes * 60)
        scheduler_process(fn, fn_kwargs, schedule_times)
