import connexion
from connexion import NoContent

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from power_usage import PowerUsage
from location import Location
import datetime

import yaml
import logging
import logging.config

# Load the app_conf.yml configuration 
with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

# Load the log_conf.yml configuration 
with open('log_conf.yml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

# Create a logger for this file
logger = logging.getLogger('basicLogger')

# Create the database connection
DB_ENGINE = create_engine(f"mysql+pymysql://"
                          f"{app_config['datastore']['user']}:"
                          f"{app_config['datastore']['password']}@"
                          f"{app_config['datastore']['hostname']}:"
                          f"{app_config['datastore']['port']}/"
                          f"{app_config['datastore']['db']}")

Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)


def report_power_usage_reading(body):
    """ Receives a power usage reading """

    session = DB_SESSION()

    power_usage_instance = PowerUsage(body['device_id'],
                                      body['device_type'],
                                      body['timestamp'],
                                      body['power_data']['energy_out_Wh'],
                                      body['power_data']['power_W'],
                                      body['power_data']['state_of_charge_%'],
                                      body['power_data']['temperature_C'],
                                      body['trace_id'])

    session.add(power_usage_instance)

    logger.debug(f"Stored event power_usage request with a trace_id of {body['trace_id']}")

    session.commit()
    session.close()

    return NoContent, 201


def report_location_reading(body):
    """ Receives a location reading """

    session = DB_SESSION()

    location_instance = Location(body['device_id'],
                                 body['device_type'],
                                 body['timestamp'],
                                 body['location_data']['gps_latitude'],
                                 body['location_data']['gps_longitude'],
                                 body['trace_id'])

    session.add(location_instance)

    logger.debug(f"Stored event location request with a trace_id of {body['trace_id']}")

    session.commit()
    session.close()

    return NoContent, 201


def retrieve_power_usage_readings(start_timestamp, end_timestamp):
    session = DB_SESSION()

    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S")
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S")

    readings = session.query(PowerUsage).filter(PowerUsage.date_created >= start_timestamp_datetime,
                                               PowerUsage.date_created < end_timestamp_datetime)
    
    results_list = []

    for reading in readings:
        results_list.append(reading.to_dict())

    session.close()

    logger.info("Query for power usage readings after %s returns %d results", start_timestamp, len(results_list))

    return results_list, 200


def retrieve_location_readings(start_timestamp, end_timestamp):
    session = DB_SESSION()

    start_timestamp_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S")
    end_timestamp_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%S")

    readings = session.query(Location).filter(Location.date_created >= start_timestamp_datetime, 
                                              Location.date_created < end_timestamp_datetime)
    
    results_list = []

    for reading in readings:
        results_list.append(reading.to_dict())

    session.close()

    logger.info("Query for location readings after %s returns %d results", start_timestamp, len(results_list))

    return results_list, 200


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8090)
