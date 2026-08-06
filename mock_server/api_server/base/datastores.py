import json
import os
import uuid
from datetime import datetime, timezone

import pymongo
import pymysql
import redis
from clickhouse_driver import Client


class DataStores:
    """将 Mock API 的业务变更同步到项目专用的四种真实数据存储。"""

    @property
    def enabled(self):
        return os.getenv('DATA_STORES_ENABLED', 'false').lower() == 'true'

    def _mysql(self):
        return pymysql.connect(
            host=os.getenv('MYSQL_HOST', '127.0.0.1'),
            port=int(os.getenv('MYSQL_PORT', '13306')),
            user=os.getenv('MYSQL_USER', 'test_user'),
            password=os.getenv('MYSQL_PASSWORD', 'test_pass'),
            database=os.getenv('MYSQL_DATABASE', 'test_automation'),
            charset='utf8mb4',
            autocommit=True,
        )

    def _redis(self):
        return redis.Redis(
            host=os.getenv('REDIS_HOST', '127.0.0.1'),
            port=int(os.getenv('REDIS_PORT', '16379')),
            decode_responses=True,
        )

    def _mongo(self):
        client = pymongo.MongoClient(
            host=os.getenv('MONGO_HOST', '127.0.0.1'),
            port=int(os.getenv('MONGO_PORT', '27018')),
            username=os.getenv('MONGO_USER', 'root'),
            password=os.getenv('MONGO_PASSWORD', 'root123456'),
            authSource='admin',
        )
        return client, client[os.getenv('MONGO_DATABASE', 'test_automation')]

    def _clickhouse(self):
        return Client(
            host=os.getenv('CLICKHOUSE_HOST', '127.0.0.1'),
            port=int(os.getenv('CLICKHOUSE_PORT', '29000')),
            user=os.getenv('CLICKHOUSE_USER', 'test_user'),
            password=os.getenv('CLICKHOUSE_PASSWORD', 'test_pass'),
            database=os.getenv('CLICKHOUSE_DATABASE', 'test_automation'),
        )

    def _record_event(self, event_type, entity_id, payload):
        event_id = str(uuid.uuid4())
        event = {
            'event_id': event_id,
            'event_type': event_type,
            'entity_id': str(entity_id),
            'payload': payload,
            'created_at': datetime.now(timezone.utc),
        }
        mongo_client, database = self._mongo()
        try:
            database.api_audit_events.insert_one(event.copy())
        finally:
            mongo_client.close()
        clickhouse = self._clickhouse()
        try:
            clickhouse.execute(
                'INSERT INTO api_events (event_id, event_type, entity_id, payload) VALUES',
                [(event_id, event_type, str(entity_id), json.dumps(payload, ensure_ascii=False))],
            )
        finally:
            clickhouse.disconnect()

    def record_user_created(self, user):
        if not self.enabled:
            return
        connection = self._mysql()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''INSERT INTO api_users (id, username, role_id, phone)
                       VALUES (%s, %s, %s, %s)
                       ON DUPLICATE KEY UPDATE role_id=VALUES(role_id), phone=VALUES(phone)''',
                    (user['id'], user['username'], user['role_id'], user['phone']),
                )
        finally:
            connection.close()
        self._record_event('USER_CREATED', user['username'], user)

    def record_order_created(self, order):
        if not self.enabled:
            return
        connection = self._mysql()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    '''INSERT INTO api_orders
                       (order_number, user_id, goods_id, quantity, amount, status)
                       VALUES (%s, %s, %s, %s, %s, 'CREATED')''',
                    (order['order_number'], order['user_id'], order['goods_id'],
                     order['quantity'], order['amount']),
                )
        finally:
            connection.close()
        self._redis().hset(f"order:{order['order_number']}", mapping={
            'user_id': order['user_id'], 'goods_id': order['goods_id'], 'status': 'CREATED'
        })
        self._record_event('ORDER_CREATED', order['order_number'], order)

    def record_order_paid(self, order_number, user_id):
        if not self.enabled:
            return
        connection = self._mysql()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE api_orders SET status='PAID' WHERE order_number=%s AND user_id=%s",
                    (order_number, user_id),
                )
                if cursor.rowcount != 1:
                    raise RuntimeError('MySQL中未找到待支付订单')
        finally:
            connection.close()
        self._redis().hset(f'order:{order_number}', 'status', 'PAID')
        self._record_event('ORDER_PAID', order_number, {'user_id': user_id})


data_stores = DataStores()
