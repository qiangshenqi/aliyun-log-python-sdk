# -×- coding: utf-8 -*-

# import rwlock
import logging

from .exceptions import CheckPointException
from .exceptions import ClientWorkerException
from ..logclient import LogClient
from ..logexception import LogException


class ConsumerClient(object):
    def __init__(self, endpoint, access_key_id, access_key, project,
                 logstore, consumer_group, consumer, security_token=None):
        self.mclient = LogClient(endpoint, access_key_id, access_key, security_token)
        self.mproject = project
        self.mlogstore = logstore
        self.mconsumer_group = consumer_group
        self.mconsumer = consumer
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_consumer_group(self, timeout, in_order):
        try:
            self.mclient.create_consumer_group(self.mproject, self.mlogstore, self.mconsumer_group,
                                               timeout, in_order)
        except LogException as e:
            # consumer group already exist
            if e.get_error_code() == 'ConsumerGroupAlreadyExist':

                try:
                    consumer_group = self.get_consumer_group()
                    # consumer group is not in server
                    if consumer_group is None:
                        raise ClientWorkerException('consumer group not exist')
                    # the consuemr group's attribute(in_order or timeout) is different from the server's
                    if consumer_group is not None \
                            and (consumer_group.is_in_order() != in_order
                                 or consumer_group.get_timeout() != timeout):
                            raise ClientWorkerException(
                                "consumer group is not agreed, AlreadyExistedConsumerGroup: {\"consumeInOrder\": " +
                                str(consumer_group.is_in_order()) + ", \"timeoutInMillSecond\": " +
                                str(consumer_group.get_timeout()) + "}")
                except LogException as e1:
                    raise ClientWorkerException("error occour when get consumer group, errorCode: " +
                                                e1.get_error_code() + ", errorMessage: " + e1.get_error_message())

            else:
                raise ClientWorkerException('error occour when create consumer group, errorCode: '
                                            + e.get_error_code() + ", errorMessage: " + e.get_error_message())

    def get_consumer_group(self):
        for consumer_group in self.mclient.list_consumer_group(self.mproject, self.mlogstore).get_consumer_groups():
            if consumer_group.get_consumer_group_name() == self.mconsumer_group:
                return consumer_group

        return None

    def heartbeat(self, shards, responce=None):
        if responce is None:
            responce = []

        try:
            responce.extend(
                self.mclient.heart_beat(self.mproject, self.mlogstore,
                                        self.mconsumer_group, self.mconsumer, shards).get_shards())
            return True
        except LogException as e:
            self.logger.warning(e)

        return False

    def update_check_point(self, shard, consumer, check_point):
        self.mclient.update_check_point(self.mproject, self.mlogstore, self.mconsumer_group,
                                        shard, check_point, consumer)

    def get_check_point(self, shard):
        check_points = self.mclient.get_check_point(self.mproject, self.mlogstore, self.mconsumer_group, shard) \
            .get_consumer_group_check_points()

        if check_points is None or len(check_points) == 0:
            raise CheckPointException('fail to get shard check point')
        else:
            return check_points[0]

    def get_cursor(self, shard_id, start_time):
        return self.mclient.get_cursor(self.mproject, self.mlogstore, shard_id, start_time).get_cursor()

    def get_begin_cursor(self, shard_id):
        return self.mclient.get_begin_cursor(self.mproject, self.mlogstore, shard_id).get_cursor()

    def get_end_cursor(self, shard_id):
        return self.mclient.get_end_cursor(self.mproject, self.mlogstore, shard_id).get_cursor()

    def pull_logs(self, shard_id, cursor, count=1000):
        return self.mclient.pull_logs(self.mproject, self.mlogstore, shard_id, cursor, count)