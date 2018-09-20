"""
    Copyright 2018 EPAM Systems, Inc.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""
import time

from syndicate.commons.log_helper import get_logger
from syndicate.core import CONN, ClientError
from syndicate.core.helper import create_pool, unpack_kwargs
from syndicate.core.resources.helper import build_description_obj

_LOG = get_logger('syndicate.core.resources.kinesis_resource')
_KINESIS_CONN = CONN.kinesis()


def create_kinesis_stream(args):
    return create_pool(_create_kinesis_stream_from_meta, 5, args)


def remove_kinesis_streams(args):
    create_pool(_remove_kinesis_stream, 5, args)


@unpack_kwargs
def _remove_kinesis_stream(arn, config):
    stream_name = config['resource_name']
    try:
        _KINESIS_CONN.remove_stream(stream_name=stream_name)
        _LOG.info('Kinesis stream %s was removed.', stream_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            _LOG.warn('Kinesis stream %s is not found', stream_name)
        else:
            raise e


@unpack_kwargs
def _create_kinesis_stream_from_meta(name, meta):
    response = _KINESIS_CONN.get_stream(name)
    if response:
        stream_status = response['StreamDescription']['StreamStatus']
        if stream_status == 'DELETING':
            _LOG.debug('Waiting for deletion kinesis stream %s...', name)
            time.sleep(120)
        else:
            _LOG.warn('%s kinesis stream exists', name)
            return {
                response['StreamARN']: build_description_obj(response,
                                                             name, meta)
            }
    _KINESIS_CONN.create_stream(stream_name=name,
                                shard_count=meta['shard_count'])
    _LOG.info('Created kinesis stream %s.', name)
    response = _KINESIS_CONN.get_stream(name)
    return {
        response['StreamARN']: build_description_obj(response, name, meta)
    }