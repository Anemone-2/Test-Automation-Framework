import json

import allure
import pymysql


class SnipeItDatabase:
    """Read-only MySQL access used for API-to-database assertions."""

    def __init__(self, settings):
        self.settings = settings

    def query_all(self, sql, params=None):
        allure.attach(
            json.dumps(
                {'sql': sql, 'params': params or ()},
                ensure_ascii=False,
                indent=2,
            ),
            name='MySQL 查询语句',
            attachment_type=allure.attachment_type.JSON,
        )
        connection = pymysql.connect(
            host=self.settings.db_host,
            port=self.settings.db_port,
            user=self.settings.db_username,
            password=self.settings.db_password,
            database=self.settings.db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, params or ())
                rows = cursor.fetchall()
        finally:
            connection.close()

        allure.attach(
            json.dumps(rows, ensure_ascii=False, indent=2, default=str),
            name='MySQL 查询结果',
            attachment_type=allure.attachment_type.JSON,
        )
        return rows

    def query_one(self, sql, params=None):
        rows = self.query_all(sql, params)
        return rows[0] if rows else None
