import os
import time
import uuid

import allure
import pymongo
import pymysql
import pytest
import redis
import requests
from clickhouse_driver import Client


pytestmark = pytest.mark.integration
BASE_URL = os.getenv('API_HOST', 'http://127.0.0.1:8787')


@pytest.fixture(scope='module')
def data_store_clients():
    status = requests.get(f'{BASE_URL}/index', timeout=5).json()
    if not status.get('data_stores_enabled'):
        pytest.skip('Mock服务未启用真实数据存储，请使用 scripts/start_mock_with_datastores.ps1 启动')

    mysql = pymysql.connect(host='127.0.0.1', port=13306, user='test_user',
                            password='test_pass', database='test_automation',
                            charset='utf8mb4', autocommit=True,
                            cursorclass=pymysql.cursors.DictCursor)
    redis_client = redis.Redis(host='127.0.0.1', port=16379, decode_responses=True)
    mongo_client = pymongo.MongoClient('mongodb://root:root123456@127.0.0.1:27018/?authSource=admin')
    clickhouse = Client(host='127.0.0.1', port=29000, user='test_user',
                        password='test_pass', database='test_automation')
    yield mysql, redis_client, mongo_client, clickhouse
    mysql.close()
    mongo_client.close()
    clickhouse.disconnect()


@allure.feature('真实数据一致性校验')
def test_api_data_consistency_across_four_stores(data_store_clients):
    mysql, redis_client, mongo_client, clickhouse = data_store_clients
    username = f'consistency_{uuid.uuid4().hex[:10]}'

    with allure.step('调用登录和新增用户接口'):
        login = requests.post(f'{BASE_URL}/dar/user/login', data={
            'user_name': 'test01', 'passwd': 'admin123'
        }, timeout=10)
        login.raise_for_status()
        token = login.json()['token']
        created = requests.post(f'{BASE_URL}/dar/user/addUser', data={
            'username': username,
            'password': 'Test123456!',
            'role_id': '1001',
            'dates': '2026-12-31',
            'phone': '13800000000',
            'token': token,
        }, timeout=10)
        assert created.json()['msg_code'] == 200

    with allure.step('校验MySQL用户记录与API请求一致'):
        with mysql.cursor() as cursor:
            cursor.execute('SELECT username, role_id, phone FROM api_users WHERE username=%s', (username,))
            user_row = cursor.fetchone()
        assert user_row == {'username': username, 'role_id': '1001', 'phone': '13800000000'}

    with allure.step('调用创建订单和支付接口'):
        order_response = requests.post(f'{BASE_URL}/coupApply/cms/placeAnOrder', json={
            'goods_id': '33809635011',
            'number': 2,
            'propertyChildIds': '2:9',
            'inviter_id': 127839112,
            'price': '239.00',
            'freight_insurance': '0.00',
            'discount_code': '002399',
            'consignee_info': {'name': '张三', 'phone': 13800000000, 'address': '北京市海淀区'},
        }, timeout=10)
        order_response.raise_for_status()
        order_data = order_response.json()
        assert order_data['error_code'] == '0000'
        order_number = order_data['orderNumber']
        user_id = order_data['userId']

        paid = requests.post(f'{BASE_URL}/coupApply/cms/orderPay', json={
            'orderNumber': order_number, 'userId': user_id, 'timeStamp': int(time.time())
        }, timeout=10)
        assert paid.json()['error_code'] == '0000'

    with allure.step('校验MySQL订单状态和Redis缓存一致'):
        with mysql.cursor() as cursor:
            cursor.execute('SELECT goods_id, quantity, status FROM api_orders WHERE order_number=%s',
                           (order_number,))
            order_row = cursor.fetchone()
        assert order_row == {'goods_id': '33809635011', 'quantity': 2, 'status': 'PAID'}
        assert redis_client.hgetall(f'order:{order_number}') == {
            'user_id': user_id, 'goods_id': '33809635011', 'status': 'PAID'
        }

    with allure.step('校验MongoDB审计事件和ClickHouse事件记录'):
        mongo_events = list(mongo_client.test_automation.api_audit_events.find(
            {'entity_id': order_number}, {'_id': 0, 'event_type': 1}
        ))
        assert {item['event_type'] for item in mongo_events} == {'ORDER_CREATED', 'ORDER_PAID'}
        clickhouse_events = clickhouse.execute(
            'SELECT event_type FROM api_events WHERE entity_id=%(entity_id)s',
            {'entity_id': order_number},
        )
        assert {item[0] for item in clickhouse_events} == {'ORDER_CREATED', 'ORDER_PAID'}

    with mysql.cursor() as cursor:
        cursor.execute('DELETE FROM api_users WHERE username=%s', (username,))
        cursor.execute('DELETE FROM api_orders WHERE order_number=%s', (order_number,))
    redis_client.delete(f'order:{order_number}')
    mongo_client.test_automation.api_audit_events.delete_many(
        {'entity_id': {'$in': [username, order_number]}}
    )
