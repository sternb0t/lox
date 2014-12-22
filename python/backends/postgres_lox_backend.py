from __future__ import unicode_literals

from datetime import datetime

import psycopg2
import pytz

from python.core.errors import *

class PostgresLoxBackend(object):
    """
    A lox provider that uses PostreSQL as the backend lock store.
    Note that autocommit is not used, so that we can control transaction manually.
    """

    def __init__(self, config):
        self.config = config
        self.connection = None

    def connect(self):
        url = self.config["backend"]["postgres"]
        self.connection = psycopg2.connect(url)
        self.cursor = self.connection.cursor()
        self.ensure_schema()

    def ensure_schema(self):
        """
        1. make sure the lox table exists
        2. if not, create it
        3. if so, make sure the columns are what we expect
        4. if not, raise exception (someone else may be using this table)
        5. make sure the indexes we need are there
        """
        try:
            if self.__ensure_table():
                if self.__ensure_columns():
                    self.__ensure_pk()
        except Exception as ex:
            self.connection.rollback()
            raise
        else:
            self.connection.commit()

    def __ensure_table(self):
        """
        # 1. make sure the lox table exists
        # 2. if not, create it
        """
        if not self.__exists("public", "lox", "r"):
            self.cursor.execute("""
            CREATE TABLE lox (
                key text NOT NULL,
                acquire_ts timestamp with time zone NOT NULL,
                expire_ts timestamp with time zone NULL,
                CONSTRAINT pk_lox PRIMARY KEY (key)
            );
            """)
        return True

    def __ensure_columns(self):
        """ Test a query with the columns we expect. """
        try:
            self.cursor.execute("""SELECT key, acquire_ts, expire_ts FROM lox LIMIT 1;""")
        except psycopg2.ProgrammingError as ex:
            raise SchemaConflictException("Incorrect columns for postgres table public.lox")
        else:
            return True

    def __ensure_pk(self):
        """
        1. make sure the PK exists
        2. if not, create it
        """
        if not self.__exists("public", "pk_lox", "i"):
            self.cursor.execute("""ALTER TABLE lox ADD CONSTRAINT pk_lox PRIMARY KEY (key);""")
        return True

    def __exists(self, namespace, relname, relkind):
        self.cursor.execute("""
            SELECT EXISTS (
                SELECT 1
                FROM   pg_catalog.pg_class c
                JOIN   pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                WHERE  n.nspname = %s
                AND    c.relname = %s
                AND    c.relkind = %s
            );
        """, (namespace, relname, relkind))
        return self.cursor.fetchone()[0]

    def acquire(self, lox_name, lock_id):
        """
        insert a row into the postgres lox table to persist the lock
        commit and return a simple tuple with lock details
        """
        key = self.key(lox_name, lock_id)
        acquire_ts = datetime.now(tz=pytz.UTC)
        try:
            self.cursor.execute("""
               INSERT INTO lox (key, acquire_ts)
               VALUES (%s, %s);
            """, (key, acquire_ts)
            )
            self.connection.commit()
        except psycopg2.IntegrityError as ex:
            self.connection.rollback()
            raise LockInUseException("Lock {} has been acquired previously, possibly by another thread/process, and is not available.".format(key))
        else:
            return (lox_name, lock_id, acquire_ts)

    def release(self, lock):
        """
        unpack simple lock tuple
        delete the corresponding row
        commit and return None
        """
        (lox_name, lock_id, acquire_ts) = lock
        key = self.key(lox_name, lock_id)
        self.cursor.execute("""
           DELETE FROM lox
           WHERE key = %s and acquire_ts = %s;
        """, (key, acquire_ts)
        )
        self.connection.commit()

    def clear(self, lox_name, lock_id):
        """
        similar to release, but not dependent on lock tuple
        """
        key = self.key(lox_name, lock_id)
        self.cursor.execute("""
           DELETE FROM lox
           WHERE key = %s;
        """, (key,)
        )
        self.connection.commit()

    def key(self, lox_name, lock_id):
        return "{}_{}".format(lox_name, lock_id)

