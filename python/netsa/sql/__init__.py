# Copyright 2008-2010 by Carnegie Mellon University

# @OPENSOURCE_HEADER_START@
# Use of the Network Situational Awareness Python support library and
# related source code is subject to the terms of the following licenses:
# 
# GNU Public License (GPL) Rights pursuant to Version 2, June 1991
# Government Purpose License Rights (GPLR) pursuant to DFARS 252.225-7013
# 
# NO WARRANTY
# 
# ANY INFORMATION, MATERIALS, SERVICES, INTELLECTUAL PROPERTY OR OTHER 
# PROPERTY OR RIGHTS GRANTED OR PROVIDED BY CARNEGIE MELLON UNIVERSITY 
# PURSUANT TO THIS LICENSE (HEREINAFTER THE "DELIVERABLES") ARE ON AN 
# "AS-IS" BASIS. CARNEGIE MELLON UNIVERSITY MAKES NO WARRANTIES OF ANY 
# KIND, EITHER EXPRESS OR IMPLIED AS TO ANY MATTER INCLUDING, BUT NOT 
# LIMITED TO, WARRANTY OF FITNESS FOR A PARTICULAR PURPOSE, 
# MERCHANTABILITY, INFORMATIONAL CONTENT, NONINFRINGEMENT, OR ERROR-FREE 
# OPERATION. CARNEGIE MELLON UNIVERSITY SHALL NOT BE LIABLE FOR INDIRECT, 
# SPECIAL OR CONSEQUENTIAL DAMAGES, SUCH AS LOSS OF PROFITS OR INABILITY 
# TO USE SAID INTELLECTUAL PROPERTY, UNDER THIS LICENSE, REGARDLESS OF 
# WHETHER SUCH PARTY WAS AWARE OF THE POSSIBILITY OF SUCH DAMAGES. 
# LICENSEE AGREES THAT IT WILL NOT MAKE ANY WARRANTY ON BEHALF OF 
# CARNEGIE MELLON UNIVERSITY, EXPRESS OR IMPLIED, TO ANY PERSON 
# CONCERNING THE APPLICATION OF OR THE RESULTS TO BE OBTAINED WITH THE 
# DELIVERABLES UNDER THIS LICENSE.
# 
# Licensee hereby agrees to defend, indemnify, and hold harmless Carnegie 
# Mellon University, its trustees, officers, employees, and agents from 
# all claims or demands made against them (and any related losses, 
# expenses, or attorney's fees) arising out of, or relating to Licensee's 
# and/or its sub licensees' negligent use or willful misuse of or 
# negligent conduct or willful misconduct regarding the Software, 
# facilities, or other rights or assistance granted by Carnegie Mellon 
# University under this License, including, but not limited to, any 
# claims of product liability, personal injury, death, damage to 
# property, or violation of any laws or regulations.
# 
# Carnegie Mellon University Software Engineering Institute authored 
# documents are sponsored by the U.S. Department of Defense under 
# Contract F19628-00-C-0003. Carnegie Mellon University retains 
# copyrights in all material produced under this contract. The U.S. 
# Government retains a non-exclusive, royalty-free license to publish or 
# reproduce these documents, or allow others to do so, for U.S. 
# Government purposes only pursuant to the copyright license under the 
# contract clause at 252.227.7013.
# @OPENSOURCE_HEADER_END@

import os
import re
import threading
import urllib

class sql_exception(Exception): 
    """
    Specific exceptions generated by :mod:`netsa.sql` derive from this.
    """
    pass

class sql_no_driver_exception(sql_exception):
    """
    This exception is raised when no driver is installed that can
    handle a URL opened via :func:`db_connect`.
    """
    pass

class sql_invalid_uri_exception(sql_exception):
    """
    This exception is raised when the URI passed to :func:`db_connect`
    cannot be parsed.
    """
    pass

class db_driver(object):
    """
    A database driver, which holds the responsibility of deciding
    which database URLs it will attempt to open, and returning
    :class:`db_connection` objects when a connection is successfully
    opened.
    """
    __slots__ = """
    """.split()
    def can_handle(self, uri_scheme):
        """
        Returns ``True`` if this :class:`db_driver` believes it can
        handle this database URI scheme.
        """
        return False
    def connect(self, uri, user, password):
        """
        Returns ``None`` if this :class:`db_driver` cannot handle this
        database URI, or a :class:`db_connection` subclass instance
        connected to the database if it can.  The *user* and
        *password* parameters passed in via this call override any
        values from the URI.
        """
        return None
    def create_pool(self, uri, user, password, **params):
        """
        Returns ``None`` if this :class:`db_driver` does not support
        pooled connections or cannot handle this database URI, or a
        :class:`db_pool` subclass instance which can be used to obtain
        connections from a pool.  The *user* and *password* parameters
        and any other parameters passed in via this call override any
        values from the URI.
        """
        return None

class db_connection(object):
    """
    An open database connection, returned by :func:`db_connect`.
    """
    __slots__ = """
        _driver
        _variants
    """.split()
    def __init__(self, driver, variants):
        if not isinstance(driver, db_driver):
            raise TypeError("db_connection must be created based on db_driver")
        self._driver = driver
        self._variants = variants
    def get_driver(self):
        """
        Returns the :class:`db_driver` used to open this connection.
        """
        return self._driver
    def clone(self):
        """
        Returns a fresh open :class:`db_connection` open to the same
        database with the same options as this connection.
        """
        raise NotImplementedError("db_connection.clone")
    def execute(self, query_or_sql, **params):
        """
        Executes the given SQL query (either a SQL string or a query
        compiled with :class:`db_query`) with the provided variable
        bindings for side effects.  Returns a :class:`db_result`
        result set if the query returns a result set, an :class:`int`
        with the number of rows affected if available, or ``None``
        otherwise.
        """
        raise NotImplementedError("db_connection.execute")
    def commit(self):
        """
        Commits the current database transaction in progress.  Note
        that if a :class:`db_connection` closes without :meth:`commit`
        being called, the transaction will automatically be rolled
        back.
        """
        raise NotImplementedError("db_connection.commit")
    def rollback(self):
        """
        Rolls back the current database transaction in progress.  Note
        that if a :class:`db_connection` closes without :meth:`commit`
        being called, the transaction will automatically be rolled
        back.
        """
        raise NotImplementedError("db_connection.rollback")
    def get_variants(self):
        """
        Returns which variant tags are associated with this connection.
        """
        return self._variants
    def __del__(self):
        """
        Roll back any uncommitted changes in the connection.
        """
        self.rollback()
        
class db_pool(object):
    """
    A pool of database connections for a single specific connection
    specification and pool configuration.  See :func:`db_create_pool`.
    """
    __slots__ = """
        _pool
    """.split()
    def __init__(self, driver):
        if not isinstance(driver, db_driver):
            raise TypeError("db_pool must be created based on db_driver")
        self._driver = driver
    def get_driver(self):
        """
        Returns the :class:`db_driver` used to open this connection.
        """
        return self._driver
    def connect(self):
        """
        Returns a :class:`db_connection` subclass instance from the
        pool, open on the database specified when the pool was
        created.
        """
        raise NotImplementedError("db_pool.connect")

class db_result(object):
    """
    A database result set, which may be iterated over.
    """
    __slots__ = """
        _connection
        _query
        _params
    """.split()
    def __init__(self, connection, query, params):
        if not isinstance(connection, db_connection):
            raise TypeError("db_result must be provided with db_connection")
        if isinstance(query, db_query):
            self._query = query
        else:
            self._query = db_query(query)
        self._connection = connection
        self._params = dict(params)
    def get_connection(self):
        """
        Returns the :class:`db_connection` which produced this result
        set.
        """
        return self._connection
    def get_query(self):
        """
        Returns the :class:`db_query` which was executed to produce
        this result set.  (Note that if a string query is given to
        :meth:`db_connection.execute`, it will automatically be
        wrapped in a :class:`db_query`, so this is always a
        :class:`db_query`.)
        """
        return self._query
    def get_params(self):
        """
        Returns the :class:`dict` of params which was given when this
        query was executed.
        """
        return self._params
    def __iter__(self):
        """
        Returns an iterator over the rows of this result set.  Each
        row returned is a :class:`tuple` with one item for each
        column.  If there is only one column in the result set, a
        tuple of one column is returned. (e.g. ``(5,)``, not just
        ``5`` if there is a single column with the value five in it.)

        It is an error to attempt to iterate over a result set more
        than once, or multiple times at once.
        """
        raise NotImplementedError("db_result.__iter__")

def register_decoder(type_name, decode_func, **variants):
    pass

def unregister_decoder(type_name):
    pass

_drivers = []
_drivers_lock = threading.RLock()
_drivers_init_done = False

def _drivers_init():
    global _drivers_init_done
    _drivers_lock.acquire()
    try:
        if _drivers_init_done:
            return
        # Find drivers and load them if possible, from the path of the
        # netsa.sql module.
        for d in __path__:
            for p in os.listdir(d):
                try:
                    if p.startswith("driver_") and p.endswith(".py"):
                        __import__("netsa.sql." + p[:-3], globals())
                except:
                    pass
        _drivers_init_done = True
    finally:
        _drivers_lock.release()

def register_driver(driver):
    """
    Registers a :class:`db_driver` database driver object with the
    :mod:`netsa.sql` module.  Driver modules generally register
    themselves, and this function is only of interest to driver
    writers.
    """
    _drivers_lock.acquire()
    try:
        if driver not in _drivers:
            _drivers.append(driver)
    finally:
        _drivers_lock.release()

def unregister_driver(driver):
    """
    Removes a :class:`db_driver` database driver object from the set
    of drivers registered with the :mod:`netsa.sql` module.
    """
    _drivers_lock.acquire()
    try:
        _drivers.remove(driver)
    finally:
        _drivers_lock.release()

def get_drivers():
    """
    Returns a list of registered drivers.
    """
    _drivers_lock.acquire()
    try:
        if not _drivers_init_done:
            _drivers_init()
        return list(_drivers)
    finally:
        _drivers_lock.release()

def get_encoders():
    _encoders_lock.acquire()
    try:
        return dict(_encoders)
    finally:
        _encoders_lock.release()

def get_decoders():
    _decoders_lock.acquire()
    try:
        return dict(_decoders)
    finally:
        _decoders_lock.release()

def db_connect(uri, user=None, password=None):
    """
    Given a database URI and an optional *user* and *password*,
    attempts to connect to the specified database and return a
    :class:`db_connection` subclass instance.

    If a user and password are given in this call as well as in the
    URI, the values given in this call override the values given in
    the URI.
    
    Database URIs have the form::

        <scheme>://<user>:<password>@hostname:port/<path>;<param>=<value>;...?<query>#<fragment>

    Various pieces can be left out in various ways.  Typically, the
    following form is used for databases with network addresses::

        <scheme>://[user[:password]@]hostname[:port]/<dbname>[;<parameters>]

    While the following form is used for databases without network
    addresses, or sometimes for connections to databases on the local
    host::

        <scheme>:<dbname>[;user=<user>][;password=<password>][;<params>]

    The user and password may always be given either in the network
    location or in the params.  Values given in the :func:`db_connect`
    call override either of those, and values given in the network
    location take priority over those given in the params.

    Refer to a specific database driver for details on what URI scheme
    to use, and what other params or URI pieces may be meaningful.
    """
    parsed_uri = db_parse_uri(uri)
    for d in get_drivers():
        if d.can_handle(parsed_uri['scheme']):
            return d.connect(uri, user, password)
    no_driver = sql_no_driver_exception(
        "No database driver for scheme %s found." % repr(parsed_uri['scheme']))
    raise no_driver

def db_create_pool(uri, user=None, password=None, **params):
    """
    Given a database URI, an optional *user* and *password*, and
    additional parameters, creates a driver-specific connection pool.
    Returns a :class:`db_pool` from which connections can be obtained.

    If a user and password (or other parameter) is given in this call
    as well as in the URI, the values given in this call override the
    values given in the URI.

    See :func:`db_connect` for details on database URIs.
    """
    parsed_uri = db_parse_uri(uri)
    for d in get_drivers():
        if d.can_handle(parsed_uri['scheme']):
            pool = d.create_pool(uri, user, password, **params)
            if pool:
                return pool
    no_driver = sql_no_driver_exception(
        "No pooled database driver for scheme %s found." %
        repr(parsed_uri['scheme']))
    raise no_driver

query_param_exp = r"(?xsm) : [a-zA-Z_][a-zA-Z_0-9]*"
query_quote_exp = r"(?xsm) ' (?: [^'\\] | \\. | '' | '[ \t]*\n[ \t*]') * ' "
query_other_exp = r"(?xsm) ([^:'] | ::)+"

query_param_re = re.compile(query_param_exp)
query_quote_re = re.compile(query_quote_exp)
query_other_re = re.compile(query_other_exp)

def _map_params(sql, param_func, other_func=None):
    # Convert query in a general way, calling param_func on each
    # param and putting what param_func returns into the
    # result.
    if other_func == None:
        def noop(x):
            return x
        other_func = noop
    (i, l, m) = (0, len(sql), True)
    result = ""
    while m and i < l:
        m = query_param_re.match(sql, i)
        if m:
            result += param_func(m.group()[1:])
            i = m.end()
            continue
        m = query_quote_re.match(sql, i)
        if m:
            result += other_func(m.group())
            i = m.end()
            continue
        m = query_other_re.match(sql, i)
        if m:
            result += other_func(m.group())
            i = m.end()
            continue
        # No matches.  Accept that, and pass through characters until
        # we match again.
        m = True
        result += other_func(sql[i])
        i += 1
    return result

def _map_params_positional(sql, param_func, other_func=None):
    param_names = []
    def param_func_2(param_name):
        param_names.append(param_name)
        return param_func(param_name)
    return (_map_params(sql, param_func_2, other_func), param_names)

class db_query(object):
    """
    A :class:`db_query` represents a "compiled" database query, which
    will be used one or more times to make requests.

    Whenever a query is executed using the
    :meth:`db_connection.execute` method, it may be provided as either
    a string or as a :class:`db_query` object.  If an object is used,
    it can represent a larger variety of possible behaviors.  For
    example, it might give both a "default" SQL to run for the query,
    but also several specific versions meant to work with or around
    features of specific RDBMS products.  For example::

        test_query = db_query(
            """'"""'"""
                select * from blah
            """'"""'""",
            postgres="""'"""'"""
                select * from pg_blah
            """'"""'""",
            oracle="""'"""'"""
                select rownum, * from ora_blah
            """'"""'""")

    A :class:`db_query` object is a callable object.  If called on a
    connection, it will execute itself on that connection.  Specifically::

        test_query(conn, ...)

    has the same effect as::

        conn.execute(test_query, ...)
    """
    __slots__ = """
        _sql
        _variants
    """.split()
    def __init__(self, sql, **variants):
        self._sql = sql
        self._variants = variants
    def __call__(self, _conn, **params):
        """
        Execute this :class:`db_query` on the given
        :class:`db_connection` with parameters.
        """
        return _conn.execute(self, **params)
    def get_variant_sql(self, accepted_variants):
        """
        Given a list of accepted variant tags, returns the most
        appropriate SQL for this query.  Specifically, this returns
        the first variant SQL given in the query which is acceptable,
        or the default SQL if none is acceptable.
        """
        for v in accepted_variants:
            if v in self._variants:
                return self._variants[v]
        return self._sql
    def get_variant_qmark_params(self, accepted_variants, params):
        """
        Like :meth:`get_variant_format_parms`, but for the DB API 2.0
        'format' paramstyle (i.e. ``%s`` placeholders).  This also
        escapes any percent signs originally present in the query.
        """
        sql = self.get_variant_sql(accepted_variants)
        def param_func_qmark(param_name):
            return "?"
        (sql, param_names) = _map_params_positional(sql, param_func_qmark)
        return (sql, [params[p] for p in param_names])
    def get_variant_numeric_params(self, accepted_variants, params):
        """
        Like :meth:`get_variant_format_params`, but for the DB API 2.0
        'numeric' paramstyle (i.e. ``:<n>`` placeholders).
        """
        sql = self.get_variant_sql(accepted_variants)
        param_num = [0]
        def param_func_numeric(param_name):
            param_num[0] += 1
            return ":%d" % param_num[0]
        (sql, param_names) = _map_params_positional(sql, param_func_numeric)
        return (sql, [params[p] for p in param_names])
    def get_variant_named_params(self, accepted_variants, params):
        """
        Like :meth:`get_variant_format_params`, but for the DB API 2.0
        'named' paramstyle (i.e. ``:<name>`` placeholders).  Note that
        this paramstyle is the native style required by the
        :mod:`netsa.sql` API.
        """
        sql = self.get_variant_sql(accepted_variants)
        def param_func_named(param_name):
            return ":%s" % param_name
        sql = _map_params(sql, param_func_named)
        return (sql, params)
    def get_variant_format_params(self, accepted_variants, params):
        """
        Converts the SQL and params of this query to a form
        appropriate for databases that use the DB API 2.0 'format'
        paramstyle (i.e. ``%s`` placeholders).  Given a list of
        accepted variants and a dict of params, this returns the
        appropriate SQL with param placeholders converted to 'format'
        style, and a list of params suitable for filling those
        placeholders.
        """
        sql = self.get_variant_sql(accepted_variants)
        def other_func_format(x):
            return x.replace('%', '%%')
        def param_func_format(param_name):
            return "%s"
        (sql, param_names) = \
            _map_params_positional(sql, param_func_format, other_func_format)
        return (sql, [params[p] for p in param_names])
    def get_variant_pyformat_params(self, accepted_variants, params):
        """

        Like :meth:`get_variant_format_params`, but for the DB API 2.0
        'pyformat' paramstyle (i.e. ``%(<name>)s`` placeholders).
        This also escapes any percent signs originally present in the
        query.

        """
        sql = self.get_variant_sql(accepted_variants)
        def other_func_pyformat(x):
            return x.replace('%', '%%')
        def param_func_pyformat(param_name):
            return "%%(%s)s" % param_name
        sql = _map_params(sql, param_func_pyformat, other_func_pyformat)
        return (sql, params)

# <scheme>://<netloc>/<path>[;<params>][?<query>][#<fragment>]

def db_parse_uri(uri):
    (scheme, user, password, host, port, path,
     params, query, frag) = (None,) * 9
    i = uri.find(':')
    if i < 0:
        invalid_uri = sql_invalid_uri_exception(
            "Invald database URI: missing access scheme in %s" % repr(uri))
        raise invalid_uri
    (scheme, uri) = (uri[:i].lower(), uri[i+1:])
    if uri.startswith('//'):
        uri = uri[2:]
        for c in '/?#':
            i = uri.find(c)
            if i >= 0:
                break
        else:
            i = len(uri)
        (host, uri) = (uri[:i], uri[i:])
        i = host.find('@')
        if i >= 0:
            (user, host) = (host[:i], host[i+1:])
            i = user.find(':')
            if i >= 0:
                (user, password) = (user[:i], user[i+1:])
        i = host.find(':')
        if i >= 0:
            (host, port) = (host[:i], host[i+1:])
    i = uri.find('#')
    if i >= 0:
        (uri, frag) = (uri[:i], uri[i+1:])
    i = uri.find('?')
    if i >= 0:
        (uri, query) = (uri[:i], uri[i+1:])
    i = uri.find(';')
    if i >= 0:
        (uri, params) = (uri[:i], uri[i+1:])
    path = uri
    # Pre-split params and query
    if params != None:
        params = list(tuple(urllib.unquote(x) for x in p.split('=',1))
                      for p in params.split(';'))
    else:
        params = []
    if query != None:
        query = list(tuple(urllib.unquote_plus(x) for x in p.split('=',1))
                     for p in query.split('&'))
    else:
        query = []
    return {
        'scheme': scheme,
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'path': path,
        'params': params,
        'query': query,
        'fragment': frag,
    }

# Bring in the deprecated legacy connection function
from netsa.sql.legacy import connect_uri

__all__ = """

    sql_exception
    sql_no_driver_exception
    sql_invalid_uri_exception

    db_connect
    db_create_pool
    db_query

    connect_uri

""".split()
