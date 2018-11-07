#!/usr/bin/env python3
# copyright 2018, Matthew Silvey, matthew@redroach.net

from boto3 import Session
from argparse import ArgumentParser
import sys
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.ERROR)


def setup_session(aws_profile, aws_region):
    try:
        sess = Session(region_name=aws_region, profile_name=aws_profile)
    except Exception as e:
        logger.error('Unknown error: {}'.format(e))
        sys.exit(1)
    return sess

def setup_ec2client(session):
    try:
        client = session.client('ec2')
    except Exception as e:
        logger.error('Unknown error: {}'.format(e))
        sys.exit(1)
    return client

def list_regions(session):
    try:
        regions = session.get_available_regions('s3')
    except Exception as e:
        logger.error('Unknown error: {}'.format(e))
        sys.exit(1)
    return regions

def list_instances(aws_profile, region, ip_range_glob):
    try:
        session = setup_session(aws_profile, region)
        client = setup_ec2client(session)
        instance_list = client.describe_instances(
            Filters=[ {'Name': 'instance-state-name', 'Values': ['running']},
                      {'Name': 'private-ip-address', 'Values': [ip_range_glob]}]
        )
    except Exception as e:
        logger.error('Unknown error: {}'.format(e))
        sys.exit(1)
    return instance_list

def main():

    parser = ArgumentParser()
    parser.add_argument('-r', default='us-west-2', type=str, dest='aws_region', help='AWS Region to use')
    parser.add_argument('-p', default='default', type=str, dest='aws_profile', help='AWS Profile to use')
    parser.add_argument('-i', default='10.*', type=str, dest='ip_address_glob', help='IP Address glob to filter on')
    args = parser.parse_args()

    session = setup_session(args.aws_profile, args.aws_region)
    regions = list_regions(session)
    for region in regions:
        list = list_instances(args.aws_profile, region, args.ip_address_glob)
        if list['Reservations']:
            for instance in list['Reservations'][0]['Instances']:
                print('Region: {} has instance id: {}'.format(region, instance['InstanceId']))
        else:
            print('Region: {}, has no running nodes matching pattern: {}'.format(region, args.ip_address_glob))

if __name__ == '__main__':
    main()


