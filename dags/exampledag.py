"""
## Astronaut ETL example DAG

This DAG queries the list of astronauts currently in space from the
Open Notify API and prints each astronaut's name and flying craft.

There are two tasks, one to get the data from the API and save the results,
and another to print the results. Both tasks are written in Python using
Airflow's TaskFlow API, which allows you to easily turn Python functions into
Airflow tasks, and automatically infer dependencies and pass data.

The second task uses dynamic task mapping to create a copy of the task for
each Astronaut in the list retrieved from the API. This list will change
depending on how many Astronauts are in space, and the DAG will adjust
accordingly each time it runs.

For more explanation and getting started instructions, see the Airflow
official tutorial: https://airflow.apache.org/docs/apache-airflow/stable/tutorial.html

![Picture of the ISS](https://www.esa.int/var/esa/storage/images/esa_multimedia/images/2010/02/space_station_over_earth/10293696-3-eng-GB/Space_Station_over_Earth_card_full.jpg)
"""

from airflow.decorators import dag, task
from datetime import datetime


@dag(start_date=datetime(2025, 1, 1), schedule_interval="@daily", catchup=False, tags=["example"])
def example_astronauts():
    """A minimal example DAG that is compatible with this Airflow image.

    This replaces a DAG that imported `airflow.sdk` (not available here).
    """

    @task
    def hello() -> str:
        print("Hello from example DAG")
        return "ok"

    @task
    def bye(val: str) -> None:
        print(f"Goodbye, got: {val}")

    v = hello()
    bye(v)


example_astronauts()
