#!/usr/bin/env python3

# copyright 2018, matthew silvey matthew@redroach.net

from boto3 import Session
import sys
import logging
import datetime
from argparse import ArgumentParser
from pprint import pprint

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

def setup_ce_client(session):
    try:
        client = session.client('ce')
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

def get_res_coverage(ce_client, start, end, granularity):
    # https://github.com/aws-samples/aws-cost-explorer-report/blob/master/src/lambda.py
    coverage = []
    try:
        response = ce_client.get_reservation_coverage(
            TimePeriod={
                'Start': start,
                'End': end
            },
            Granularity=granularity,
        )
        coverage.append(response['CoveragesByTime'])
        while 'nextToken' in response:
            nextToken = response['nextToken']
            response = ce_client.get_reservation_coverage(
                TimePeriod={
                    'Start': start,
                    'End': end
                },
                Granularity=granularity,
                NextPageToken=nextToken
            )
            coverage.append(response['CoveragesByTime'])
            if 'nextToken' in response:
                nextToken = response['nextToken']
            else:
                nextToken = False
    except Exception as e:
        logger.error('Unknown error: {}'.format(e))
        sys.exit(1)
    return coverage

def get_cost(ce_client, start, end, granularity):
    cost = []
    try:
        rawcost = ce_client.get_cost_and_usage(
            TimePeriod={
                'Start': start,
                'End': end},
            Granularity=granularity,
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'LINKED_ACCOUNT'
                },
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }]
        )
        cost.append(rawcost['ResultsByTime'])
        while 'nextToken' in rawcost:
            nextToken = rawcost['nextToken']
            rawcost = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start,
                    'End': end},
                Granularity=granularity,
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {
                        'Type': 'DIMENSION',
                        'Key': 'LINKED_ACCOUNT'
                    },
                    {
                        'Type': 'DIMENSION',
                        'Key': 'SERVICE'
                    }]
            )
            if 'nextToken' in rawcost:
                nextToken = rawcost['nextToken']
            else:
                nextToken = False
    except Exception as e:
        logger.error('Unknown error: {}'.format(e))
        sys.exit(1)
    return cost



def main():

    parser = ArgumentParser()
    parser.add_argument('-r', default='us-west-2', type=str, dest='aws_region', help='AWS Region to use')
    parser.add_argument('-p', default='default', type=str, dest='aws_profile', help='AWS Profile to use')
    parser.add_argument('-d', default=30, type=int, dest='days', help='Number of days to check')
    parser.add_argument('-g', default='DAILY', type=str, dest='granularity', help='Daily or Monthly granularity for results')
    args = parser.parse_args()

    session = setup_session(args.aws_profile, args.aws_region)
    ce = setup_ce_client(session)
    now = datetime.datetime.utcnow()
    start = (now - datetime.timedelta(days=args.days)).strftime('%Y-%m-%d')
    end = now.strftime('%Y-%m-%d')
    coverage_blob = get_res_coverage(ce, start, end, args.granularity)
    pprint(coverage_blob)
    cost_blob = get_cost(ce, start,end, args.granularity)
    pprint(cost_blob)



if __name__ == '__main__':
    main()


