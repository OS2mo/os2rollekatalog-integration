#
# Copyright (c) 2019, Magenta ApS
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
import requests

from os2mo_tools import mo_api


ROOT_ORG_UNIT = '97337de5-6096-41f9-921e-5bed7a140d85'
ROLLE_KATALOG_URL = "https://192.168.122.193:8090/api/organisation"
AD_SYSTEM_NAME = "Active Directory"


def get_user_id(employee):
    for system in employee.it:
        if system['itsystem']['name'] == AD_SYSTEM_NAME:
            return system['user_key']


def get_title(employee):
    for e in employee.engagement:
        # TODO: Change this when we have a preferred engagement.
        return e['job_function']['name']


def get_orgunit_structure(ou_uuid):
    """Retrieve an org unit as a tree dict for Rollekataloget.

    The exact format is described in the API documentation for
    OS2Rollekatalog, which may be found at this address:
        https://bitbucket.org/os2offdig/os2rollekatalog/src/\
        2bf817ee8df801214ae2b6d6f42bfe154056ff93/doc/api.html?\
        at=master&fileviewer=file-view-default

    Retrieve the info for current unit and recursively for children.
    """
    ou = mo_api.OrgUnit(ou_uuid)
    engagements = ou.engagement
    name = ou.json['name']

    employees = []
    for e in engagements:
        employee_name = e['person']['name']
        employee_uuid = e['person']['uuid']
        employee = mo_api.Employee(e['person']['uuid'])

        user_id = get_user_id(employee)
        title = get_title(employee)
        if user_id:
            """Only append employees with valid User ID."""
            employees.append({
                'uuid': employee_uuid, 'name': employee_name,
                'user_id': user_id, 'title': title
            })

    return {
        'uuid': ou_uuid,
        'name': name,
        'employees': employees,
        'kle-performing': [],
        'kle-interest': [],
        'children': [
            get_orgunit_structure(c['uuid']) for c in ou.children
        ]
    }


def main():
    """Main function - download from OS2MO and export to OS2Rollekatalog."""
    print("Reading org ....")
    organization = get_orgunit_structure(ROOT_ORG_UNIT)
    session = requests.Session()
    print("Writing to Rollekataloget ...")
    result = session.post(
        ROLLE_KATALOG_URL, json=organization, headers={'ApiKey': 'Test1234'},
        verify=False
    )
    print("Done!")
    print(result, result.text)


if __name__ == '__main__':
    main()
