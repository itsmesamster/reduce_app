# standard
from threading import Thread

# 3rd party
import uvicorn

# project
from monitor.metrics import monitor_api  #  noqa: F401


if __name__ == "__main__":
    monitor = Thread(
        target=uvicorn.run,
        kwargs={
            "app": "monitor.metrics:monitor_api",
            "host": "0.0.0.0",
            "port": 5000,
        },
    )

    monitor.start()

    # api = Thread(
    #     target=uvicorn.run,
    #     kwargs={
    #         "app": "monitor.api.server:api",
    #         "host": "0.0.0.0",
    #         "port": 8123,
    #     },
    # )

    # uvicorn.run("app.ext.ahcp5.api.server:api",
    #             host="0.0.0.0",
    #             port=8123,
    #             # reload  = True,
    #             )
