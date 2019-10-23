#
# Copyright (c) 2019, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import csv
import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import requests

from os2mo_tools import mo_api

logger = logging.getLogger(__name__)

EMPLOYEE_MAPPING_PATH = os.environ.get("MOX_ROLLE_EMPLOYEE_MAPPING_PATH")
AD_SYSTEM_NAME = os.environ.get("MOX_ROLLE_AD_SYSTEM_NAME")
OS2MO_URL = os.environ.get("MOX_ROLLE_OS2MO_URL")
OS2MO_API_KEY = os.environ.get("MOX_ROLLE_OS2MO_API_KEY")
ROLLEKATALOG_URL = os.environ.get("MOX_ROLLE_ROLLEKATALOG_URL")
ROLLEKATALOG_API_KEY = os.environ.get("MOX_ROLLE_ROLLEKATALOG_API_KEY")
LOG_PATH = os.environ.get("MOX_ROLLE_LOG_FILE", "log.log")


def init_log():
    logger = logging.getLogger(__name__)

    logging.getLogger("urllib3").setLevel(logging.INFO)

    log_format = logging.Formatter(
        "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
    )

    stdout_log_handler = logging.StreamHandler()
    stdout_log_handler.setFormatter(log_format)
    stdout_log_handler.setLevel(logging.DEBUG)  # this can be higher
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(stdout_log_handler)

    # The activity log is for everything that isn't debug information. Only
    # write single lines and no exception tracebacks here as it is harder to
    # parse.
    try:
        log_file_handler = RotatingFileHandler(filename=LOG_PATH, maxBytes=1000000)
    except OSError as err:
        logger.critical("MOX_ROLLE_LOG_FILE: %s: %r", err.strerror, err.filename)
        sys.exit(3)

    log_file_handler.setFormatter(log_format)
    log_file_handler.setLevel(logging.DEBUG)
    logging.getLogger().addHandler(log_file_handler)


def get_user_id(e):
    it = e.it

    active_directory_users = list(
        filter(lambda it: it["itsystem"]["name"] == AD_SYSTEM_NAME, it)
    )

    if active_directory_users:
        if len(active_directory_users) > 1:
            logger.warning(
                "More than one Active Directory user for employee {}".format(e.uuid)
            )
        return it[0]["user_key"]

    return None


def get_employee_mapping():
    mapping_path = EMPLOYEE_MAPPING_PATH
    try:
        with open(mapping_path) as f:
            csv_reader = csv.DictReader(f, delimiter=";")
            content = {line["mo_uuid"]: line["ad_guid"] for line in csv_reader}
    except FileNotFoundError as err:
        logger.critical("%s: %r", err.strerror, err.filename)
        sys.exit(3)
    return content


def get_org_units(connector):
    org_units = connector.get_ous()

    converted_org_units = []
    for org_unit in org_units:

        org_unit_uuid = org_unit["uuid"]
        # Fetch the OU again, as the 'parent' field is missing in the data
        # when listing all org units
        ou = connector.get_ou_connector(org_unit_uuid)

        def get_parent_org_unit_uuid(ou):
            parent = ou.json["parent"]
            if parent:
                return parent["uuid"]
            return None

        def get_manager(ou):
            managers = ou.manager
            if not managers:
                return None
            if len(managers) > 1:
                logger.warning(
                    "More than one manager exists for {}".format(org_unit_uuid)
                )
            manager = managers[0]

            person = manager.get("person")
            if not person:
                return None

            e = connector.get_employee_connector(person["uuid"])
            user_id = get_user_id(e)
            if not user_id:
                logger.critical(
                    "Employee {} is manager, "
                    "but has no associated AD user".format(person["uuid"])
                )
                sys.exit(3)

            return {"uuid": manager["uuid"], "userId": user_id}

        payload = {
            "uuid": org_unit_uuid,
            "name": org_unit["name"],
            "parentOrgUnitUuid": get_parent_org_unit_uuid(ou),
            "manager": get_manager(ou),
        }
        converted_org_units.append(payload)

    return converted_org_units


def get_users(connector):
    # read mapping
    mapping = get_employee_mapping()

    employees = connector.get_employees()

    converted_users = []
    for employee in employees:

        employee_uuid = employee["uuid"]
        employee_connector = connector.get_employee_connector(employee_uuid)

        def get_ext_uuid(employee_uuid):
            if not employee_uuid in mapping:
                logger.warning(
                    "Unable to find employee in mapping with UUID {}".format(
                        employee_uuid
                    )
                )
                return None
            mapped = mapping.get(employee_uuid)
            return mapped

        def get_employee_email(e):
            addresses = e.address
            emails = list(
                filter(
                    lambda address: address["address_type"]["scope"] == "EMAIL",
                    addresses,
                )
            )

            if emails:
                if len(emails) > 1:
                    logger.warning(
                        "More than one email exists for user {}".format(employee_uuid)
                    )
                return emails[0]["value"]
            return None

        def get_employee_positions(e):
            engagements = e.engagement

            converted_positions = []
            for engagement in engagements:
                converted_positions.append(
                    {
                        "name": engagement["job_function"]["name"],
                        "orgUnitUuid": engagement["org_unit"]["uuid"],
                    }
                )
            return converted_positions

        ext_uuid = get_ext_uuid(employee_uuid)
        if not ext_uuid:
            # Only import users who have an AD UUID
            continue

        payload = {
            "extUuid": ext_uuid,
            "userId": get_user_id(employee_connector),
            "name": employee["name"],
            "email": get_employee_email(employee_connector),
            "positions": get_employee_positions(employee_connector),
        }
        converted_users.append(payload)

    return converted_users


def main():
    """Main function - download from OS2MO and export to OS2Rollekatalog."""
    init_log()

    try:
        mo_connector = mo_api.Connector(OS2MO_URL, api_token=OS2MO_API_KEY)
    except requests.RequestException:
        logger.exception("An error occurred connecting to OS2mo")
        sys.exit(3)

    try:
        logger.info("Reading organisation")
        org_units = get_org_units(mo_connector)
    except requests.RequestException:
        logger.exception("An error occurred trying to fetch org units")
        sys.exit(3)
    logger.info("Found {} org units".format(len(org_units)))

    try:
        logger.info("Reading employees")
        users = get_users(mo_connector)
    except requests.RequestException:
        logger.exception("An error occurred trying to fetch employees")
        sys.exit(3)
    logger.info("Found {} employees".format(len(users)))

    payload = {"orgUnits": org_units, "users": users}

    try:
        with open("output", "a") as f:
            f.write(json.dumps(payload, indent=2))

        logger.info("Writing to Rollekataloget")
        result = requests.post(
            ROLLEKATALOG_URL,
            json=payload,
            headers={"ApiKey": ROLLEKATALOG_API_KEY},
            verify=False,
        )
        logger.info(result.json())
        result.raise_for_status()
    except requests.RequestException:
        logger.exception("An error occurred when writing to Rollekataloget")
        sys.exit(3)


if __name__ == "__main__":
    main()
