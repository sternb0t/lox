from __future__ import unicode_literals

import unittest
from datetime import datetime

import psycopg2
import pytz

from python.lox import Lox
from python.core.lock import Lock
from python.core.errors import *
from test_lox_base import LoxTestsBaseMixin

class LoxPostgresTests(LoxTestsBaseMixin, unittest.TestCase):

    def setUp(self):
        super(LoxPostgresTests, self).setUp()
        self.config = {"backend": {"postgres": "postgresql://postgres:postgres@localhost/postgres"}}
        self.lox = Lox("everythingbagel", config=self.config)
        self.lox.clear_all()

    def test_init(self):
        self.assertEqual(self.lox.name, "everythingbagel")
        self.assertEqual(self.lox.config, self.config)
        self.assertEqual(self.lox.locks, {})
        self.assertIsNone(self.lox.context_lock)

    def test_ensure_schema__basic(self):
        # make sure the lox table doesn't exist in the db
        # NOTE this is destructive, we should really run this on a test db
        self.lox.backend.cursor.execute("""
          drop table if exists lox;
        """)

        # create the table
        self.lox.backend.ensure_schema()

        # validate we can directly talk to the lox table in the db

        # first with not null expiration
        test_row = self.__insert_test_row(expire_null=False)
        db_row = self.__select_test_row(test_row, expire_null=False)
        self.assertEqual(db_row, test_row)

        # then with null expiration
        test_row = self.__insert_test_row(expire_null=True)
        db_row = self.__select_test_row(test_row, expire_null=True)
        self.assertEqual(db_row, test_row)

        # don't persist
        self.lox.backend.connection.rollback()

    def test_ensure_schema__wrong_columns(self):
        # make sure the lox table doesn't exist in the db
        # NOTE this is destructive, we should really run this on a test db

        # and create another table with the same name but different schema
        self.lox.backend.cursor.execute("""
          drop table if exists lox;
          create table lox (blah int);
        """)

        # create the table
        with self.assertRaises(SchemaConflictException):
            self.lox.backend.ensure_schema()

    def test_ensure_schema__no_pk(self):
        # make sure the lox table doesn't exist in the db
        # NOTE this is destructive, we should really run this on a test db

        # and create another table with the same name but no primary key
        self.lox.backend.cursor.execute("""
          drop table if exists lox;
          create table lox (
            key text NOT NULL,
            acquire_ts timestamp with time zone NOT NULL,
            expire_ts timestamp with time zone NULL
          );
        """)

        # create the pk
        self.lox.backend.ensure_schema()

        # make sure the pk gets created by trying to insert 2 rows with the same key
        test_row = self.__insert_test_row(expire_null=False)
        db_row = self.__select_test_row(test_row, expire_null=False)
        self.assertEqual(db_row, test_row)

        # 2nd insert should get a PK violation
        with self.assertRaises(psycopg2.IntegrityError):
            self.__do_insert(test_row)

        # don't persist
        self.lox.backend.connection.rollback()

    def __insert_test_row(self, expire_null):
        test_key = "test_{}".format(Lock.generate_id())
        test_ts = datetime.now(tz=pytz.UTC)
        if expire_null:
            test_row = (test_key, test_ts, None)
        else:
            test_row = (test_key, test_ts, test_ts)
        self.__do_insert(test_row)
        return test_row

    def __do_insert(self, test_row):
        self.lox.backend.cursor.execute("""
          insert into lox (key, acquire_ts, expire_ts)
          values (%s, %s, %s);
        """, test_row)

    def __select_test_row(self, test_row, expire_null):
        sql = """
          select * from lox
          where key = %s and acquire_ts = %s and expire_ts """
        if expire_null:
            sql += "is %s"
        else:
            sql += "= %s"
        self.lox.backend.cursor.execute(sql, test_row)
        return self.lox.backend.cursor.fetchone()


if __name__ == '__main__':
    unittest.main()
