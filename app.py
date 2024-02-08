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


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8090)
