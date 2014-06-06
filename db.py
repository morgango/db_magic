from __future__ import print_function
from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic)

from IPython.core.magic_arguments import (argument, magic_arguments, parse_argstring)

import pyodbc
import logging
from inspect import stack

@magics_class
class DbMagic(Magics):

    _most_recent_conn_alias = ''
    _default_conn_alias = ''
    _conn_info = {}
    _args = {}

    @magic_arguments()
    @argument('source', type=str, help='The identifier of the data source (optional)',default='', nargs='?')
    @argument('cmd', type=str, help='A command to be executed (optional)',default='', nargs='*')
    @argument('-src', '--source', help='The data source to use (optional).', action="store")
    @argument('-a', '--alias', help='The key to refer to this connection with', action="store")
    @argument('-def', '--default', help='The key to refer to this connection with', action="store")
    @argument('-c', '--connect', '--conn', help='Connect to this database', action="store_true")
    @argument('-d', '--disconnect', '--dis', help='Disconnect from this datbase', action="store_true")
    @argument('-t', '--type', help='Connection type (ODBC is the default)', action="store", default="odbc")
    @argument('-l', '--list', help='List things about the database.', action="store", nargs='?')
    @argument('-e', '--execute', '--exec', help='Some SQL to execute', action="store_true")
    @argument('-m', '--commit', help='Commit this transaction.', action="store_true")
    @argument('-r', '--rollback', help='Rollback this transaction.', action="store_true")
    @argument('-n', '--naked', help='Run a naked query (same as --connect --execute --fetch --disconnect)', action="store_true")
    @argument('--unsourced', help='Run an unsourced query (same as --connect --execute --fetch --disconnect)', action="store_true")
    @argument('-f', '--fetch', help='Fetch one or more records (default is all)', action="store", default=0,nargs='?')
    @argument('-u', '--uid', '--username', help='The user name to use (optional).', action="store", default='')
    @argument('-p', '--pwd', '--password', help='The password to use (optional).', action="store", default='')
    @argument('-h', '--help', help='Display help.', action="store_true")
    @argument('-v', '--verbose', help='Display debugging verbosely (same as --debug=DEBUG', action="store_true")
    @argument('--debug', help='Output debugging info', action="store", default='WARNING',nargs='?')
    @argument('-y', '--dry_run', '--dry', help='Make this a dry run', action="store_true")
    @argument('--explain', help='Give an explanation on exac', action="store_true")
    @argument('--note', help='Add a note for help with debugging', action="store", nargs="*")
    @argument('--cleanup', help='Clean up all the connections and shut down', action="store_true")

    def parse_args(self,magic_args):
        """
        parses the arguments from the ipython magic call

        Everything is pretty straightforward here except for special convienence cases
       
        %db <source> <cmd>    [or a naked query]
        %db <cmd>             [or an unsourced query]

       This is how most users would expect to call the function.  However, this means we
       have to infer a hell of a lot of things based on very little information.
       
        There are also a few challenges here:
          1. The cmd argument can be multiple words, or empty.
          2. The source argument is optional, if we just have cmd then we need to find source.
          3. The options are all optional, so we need to interpret what is really meant.

        If we have both arguments, no problem.  However, we can't really tell if this is the,
        case except by testing to see if we already have a data source that matches what is 
        specified.  If there is no match, then we can use the default data source unless
        this is a new connection.

        :param magic_args: the arguments to be parsed from @magic_arguments
        :returns: formatted string

        """

        no_alias_provided = False
        
        # parse the arguments and assign them to a class-level variable
        self._args = parse_argstring(self.parse_args, magic_args)

        logging.debug(' -- The parsed arguments are: %s' % self._args)

        #############################################################################
        # the key/value store uses the alias, so if there isn't one just set it
        # to the source so we have a uniform way of dealing with things
        #############################################################################
        if self._args.alias is None:
            logging.debug(" --- No alias provided, using %s" % (self._args.source))
            no_alias_provided = True
            self._args.alias = self._args.source

        connection_alias = self._args.alias
        connection_key = self._args.source
        connection_cmd = ' '.join(self._args.cmd)
        connection_fetch = self._args.fetch

        ##############################################################################
        # handling the special situation of %db <source> <cmd> (or a NAKED QUERY)
        #
        # We know that we:
        #
        # 1. Will have our positional arguments (either source and cmd or just cmd) defined.
        # 2. Will NOT have an existing connection with the same name.
        # 3. Will NOT have connection-specific options (like alias, connect, execute, disconnect)
        # 4. May have record-filtering options (like fetch and skip)
        # 5. May have incidental options(like debug, user, pass)
        #
        # Also, the line_magic function is set up so that if you pass multiple options, they will
        # be executed in the correct order.  For example, if you have a call like:
        #
        #   %db <source> <cmd> --connect --skip 10 --fetch --disconnect
        #
        # we can rely on the fact that things will be handled properly.
        ##############################################################################

        imply_naked_query =  \
            (self._args.source is not None) and \
            (self._args.source in \
                self.list_values( \
                    self._args.alias,  \
                    self._args.type, \
                    'sources')) and \
            (self._args.cmd is not None) and \
            (len(self._args.cmd) > 0) and \
            (connection_key not in self._conn_info.keys()) and \
            (self._args.list is None) and \
            (no_alias_provided and \
                not self._args.connect and \
                not self._args.execute and \
                not self._args.disconnect )

        if (self._args.naked or imply_naked_query ):
            logging.debug(" --- This is a naked query with source '%s' and cmd '%s'" %(connection_alias, connection_cmd))
            self._args.naked = True
            self._args.fetch = 'all'
            connection_fetch = 'all'
            logging.debug(" --- Changing fetch to %s" % (self._args.fetch))
        else:
            logging.debug(' --- This is not a naked query')

        ##############################################################################
        # handling the special situation of %db <cmd> (or an UNSOURCED QUERY)
        #
        # We know that we:
        #
        # 1. Will have our positional arguments (either source and cmd or just cmd) defined.
        # 2. Will have an existing connection with the same name.
        # 3. Will NOT have connection-specific options (like alias, connect, execute, disconnect)
        # 4. May have record-filtering options (like fetch and skip)
        # 5. May have incidental options(like debug, user, pass)
        #
        ##############################################################################
        imply_unsourced_query =  \
            (self._args.source is not None) and \
            (self._args.source not in \
                self.list_values( \
                    self._args.alias,  \
                    self._args.type, \
                    'sources')) and \
            (self._args.cmd is not None) and \
            (self._args.list is None) and \
            (no_alias_provided and \
                not self._args.cleanup and \
                not self._args.connect and \
                not self._args.execute and \
                not self._args.disconnect )

        if (imply_unsourced_query ):
            logging.debug(" --- This is an unsourced query with source '%s' and cmd '%s'" %(connection_alias, connection_cmd))
            self._args.unsourced = True
            self._args.fetch = 'all'
            connection_fetch = 'all'
            logging.debug(" --- Changing fetch to %s " % (self._args.fetch))
        else:
            logging.debug(' --- This is not a unsourced query')

        if connection_key not in self._conn_info.keys() and \
                not self._args.naked and \
                not self._args.unsourced:
            # this is not a new connection and not an established source, we assume 
            # this is a command line like %db <exec> and fix the command
            try:
                self._args.cmd.insert(0,connection_key)
                connection_cmd = ' '.join(self._args.cmd)
                logging.debug(" --- Merging %s and %s into '%s'" % (connection_key, self._args.cmd, connection_cmd))
            except:
                pass

        if self._args.unsourced:

            if len(self._args.cmd) > 0:
                self._args.cmd.insert(0,connection_key)
                connection_cmd = ' '.join(self._args.cmd)
                logging.debug(" --- Merging %s and %s into '%s'" % (connection_key, self._args.cmd, connection_cmd))

            logging.debug(" ---Assigning alias from the default as %s" % (self._default_conn_alias))
            self._args.alias = self._default_conn_alias
            connection_alias = self._args.alias

            logging.debug(" ---Assigning source from the default as %s" % (self._default_conn_alias))
            self._args.source = self._default_conn_alias
            connection_key = self._args.source

        ##############################################################################
        # make it so we can make a connection, then assume that we are using the same alias
        # until we specify a different one
        ##############################################################################
        if connection_alias == '' or connection_alias is None:
            connection_alias =  self._most_recent_conn_alias
            logging.debug(" --- Setting current alias to %s" % (connection_alias))

        ##############################################################################
        # make it so that if there is a command it will be executed, regardless of interpretation.
        ##############################################################################
        if len(connection_cmd) > 1:
            logging.debug(" --- Command is %s, setting execute to True" % connection_cmd)
            self._args.execute = True


        ##############################################################################
        # set up logging for this particular run
        ##############################################################################
        if self._args.debug is None or \
                self._args.debug.lower() == 'debug' or \
                self._args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        elif self._args.debug.lower() == 'warning':
            logging.getLogger().setLevel(logging.WARNING)
        elif self._args.debug.lower() == 'info':
            logging.getLogger().setLevel(logging.INFO)
        elif self._args.debug.lower() == 'error':
            logging.getLogger().setLevel(logging.ERROR)
        elif self._args.debug.lower() == 'critical':
            logging.getLogger().setLevel(logging.CRITICAL)
        else:
            logging.getLogger().setLevel(logging.INFO)
            logging.debug(" --- The debug level '%s' is not valid, using INFO." % self._args.debug)

        return connection_alias, connection_key, connection_cmd, connection_fetch, self._args

    def explain(self, alias, key, cmd, fetch, args, line):
        """
        Explains the operations that are going to be done as part of the command line invocation

        :param alias: the plain english name to associate with this connection
        :param type: the type of connection to use
        :param key: the key that will be used to find the correct connection.
        :param cmd: the command that will be executed 
        :param fetch: the argument for fetching data or not
        :param args: all the arguments passed to the class
        :param line: the command line used to call the class

        """

        print("Command Line called : %%db %s" % line)
        print("-------------------")
        print("Data Source to Use: %s" % args.source)
        print("Data Source Type: %s" % args.type)
        print("Data Source Alias: %s" % alias)
        print("Command to Execute: %s" % cmd)
        print("Execution Notes: %s" % str(args.note))
        print("-------------------")
        print("Open Connections: %s" % self._conn_info)
        print("-------------------")
        print("Is this a Naked Query?: %s" % args.naked)
        print("Is this a Unsourced Query?: %s" % args.unsourced)
        print("-------------------")
        print("Are we Connecting to DB?: %s" % (args.connect or args.naked))
        print("Are we Commiting Transaction?: %s" % (args.commit))
        print("Are we Fetching records?: %s" % fetch)
        print("Are we Listing values?: %s" % args.list)
        print("Are we Disconnecting from DB?: %s" % (args.disconnect or args.naked))
        print("=========================================================")

        return

    def is_registered(self, alias):
        """
        
        :param alias: the alias to verify as existing
        :returns: boolean

        """

        return alias in self._conn_info.keys()

    def is_connected(self, alias):
        """
        validates that an alias exists and has a connection
        
        :param alias: the alias to verify as a valid connection
        :returns: boolean

        """

        return self.is_registered(alias) and not (self._conn_info[alias]['connection'] is None)

    def connect_to_source(self, connection_alias, connection_type, connection_source,username,password):
        """
        Establishes a connection to a data source and removes the alias.

        :param connection_alias: the plain english name to associate with this connection
        :param connection_type: the type of connection to use
        :param connection_source: the name of an an ODBC DSN or connection string
        :param username: the username to use for a connection (optional)
        :param password: connection_source: the password to use for a connection (optional)
        :returns: formatted string

        """

        logging.debug(" -- Working with connection '%s' of type '%s'" % (connection_alias, connection_type))

        if self.is_registered(connection_alias):
            raise Exception(stack()[0][3], \
                " --- There is already a connection with the alias %s" % connection_alias)

        logging.debug(" --- Working with connection '%s' of type '%s'" % (connection_alias, connection_type))

        if connection_type.lower() == 'odbc':

            try:

                logging.debug(" ---- Attempting to connect to '%s' " % (connection_alias))

                # connect to the ODBC source

                if (len(username) > 0 and len(password) > 0):
                    new_cnxn = pyodbc.connect(connection_source,uid=username,pwd=password)
                else:
                    new_cnxn = pyodbc.connect(connection_source)

                new_cursor = new_cnxn.cursor()

                # store the results and make this the active connection
                self._conn_info[connection_alias] = \
                        {'alias' : connection_alias, \
                        'cursor' : new_cursor, \
                        'connection' :new_cnxn, \
                        'type' : connection_type }

            except pyodbc.Error, err:
                logging.error("The connection is '%s' the available connections are " % connection_alias)
                logging.error(self._conn_info)
                logging.error(err[1])
                raise err


            self._default_conn_alias = connection_alias

            logging.debug(" --- Connected data source '%s' as type '%s'"  % (connection_alias,connection_type))

        else:
            
            raise Exception(stack()[0][3], \
                    "The type provided ('%s') is not valid.  No connection made" % connection_type)

    def disconnect_from_source(self, connection_alias, connection_type):
        """
        Disconnects a particular connection to a data source and removes the alias.

        :param connection_alias: the plain english name to associate with this connection
        :param connection_type: the type of connection to use

        """

        logging.debug(" -- Working with connection '%s' of type '%s'" % (connection_alias, connection_type))

        if connection_type.lower() == 'odbc':

            if not self.is_registered(connection_alias):
                raise Exception(stack()[0][3], "There is noconnection with the alias %s" % connection_alias)
            
            try:
                logging.debug(" --- Attempting to disconnect from %s " % (connection_alias))
                cursor = self._conn_info[connection_alias]['cursor']
                cnxn = self._conn_info[connection_alias]['connection']
            except pyodbc.Error, err:
                logging.error(err[1])
                raise err

            # disconnect everything and remove the entry from the master list
            cursor.close()
            cnxn.close()
            self._conn_info.pop(connection_alias,"None")

            logging.debug(" --- Disconnected data source '%s'"  % connection_alias)

            # set the active connection to the last one created
            if len(self._conn_info.keys()) > 0:
                self._active_conn_key = self._conn_info.keys()[0]
                logging.debug(" --- Setting active key to '%s'"  % self._active_conn_key)
            else:
                self._active_conn_key = None

        else:
            
            raise Exception(stack()[0][3], \
                    "The type provided ('%s') is not valid.  No connection made" % connection_type)

    def execute_command(self, connection_alias, connection_type, command, fetch):
        """
        Execute a command on a remote data source

        NOTE: this will not return a value, just execute the command.  Use fetch() 

        :param connection_alias: the plain english name to associate with this connection
        :param connection_type: the type of connection to use
        :param command:  the command to execute at the connection

        """

        logging.debug(" -- Working with connection '%s' of type '%s'" % (connection_alias, connection_type))

        if connection_type.lower() == 'odbc':

            if self.is_registered(connection_alias):

                logging.debug(" --- Executing '%s' on '%s'" % (command, connection_alias))

                if not self.is_connected(connection_alias):
                    raise Exception(stack()[0][3], "There is no connection with the alias %s" % connection_alias)

                if len(command) > 0:
                    try:
                        logging.debug(" --- Attempting to execute '%s' on '%s'" % (command, connection_alias))
                        cursor = self._conn_info[connection_alias]['cursor']
                        cursor.execute(command)
                    except pyodbc.Error, err:
                        logging.error(err[1])
                        raise err
                else:
                        logging.debug(" --- Skipping empty command.")
                    
            else:

                raise Exception(stack()[0][3], "The connection '%s' is not registered" % connection_alias)

        else:
            
                raise Exception(stack()[0][3], "The type provided ('%s') is not valid.  No connection made" % connection_type)


    def fetch(self, connection_alias, connection_type, fetch):
        """
        Fetch the results from a previous command.  This is always used in conjunction
        with the execute_command() function, either implicitly or explicitly.

        :param connection_alias: the plain english name to associate with this connection
        :param connection_type: the type of connection to use
        :param fetch: how many records to fetch, either a positive integer or 'all'

        """

        logging.debug(" -- Working with connection '%s' of type '%s'" % (connection_alias, connection_type))

        if connection_type.lower() == 'odbc':

            logging.debug(" --- Fetching '%s' records from '%s'" % (fetch, connection_alias))

            if not self.is_connected(connection_alias):
                logging.debug(" ---- The alias '%s' is not connected" % connection_alias)
                return

            try:

                cursor = self._conn_info[connection_alias]['cursor']
                description = []

                if (isinstance(fetch, str) or isinstance(fetch, unicode)) and 'all' in fetch:
                    logging.debug(" ---- Running cursor.fetchall()")
                    return cursor.fetchall()
                elif (long(fetch) == 0):
                    logging.debug(" ---- Running cursor.fetchall()")
                    return cursor.fetchall()
                elif long(fetch) > 0:
                    logging.debug(" ---- Running cursor.fetchmany(%s)" % long(fetch))
                    return cursor.fetchmany(long(fetch))
                else:
                    logging.debug(" ---- '%s' is an invalid number of rows to fetch" % fetch)

            except pyodbc.ProgrammingError, err:
                logging.warning(err)
                pass
            except pyodbc.Error, err:
                logging.error(err)
                raise err

        else:
            
            raise Exception(stack()[0][3], \
                    "The type provided ('%s') is not valid.  No connection made" % connection_type)

    def commit(self, connection_alias, connection_type):
        """
        commit the results from a previous command.  This is always used in conjunction
        with the execute_command() function, either implicitly or explicitly.

        :param connection_alias: the plain english name to associate with this connection
        :param connection_type: the type of connection to use

        """

        logging.debug(" -- Working with connection '%s' of type '%s'" % (connection_alias, connection_type))

        if connection_type.lower() == 'odbc':

            logging.debug(" --- commiting cursor '%s'" % (connection_alias))

            if not self.is_connected(connection_alias):
                logging.debug(" ---- The alias '%s' is not connected" % connection_alias)
                return

            try:

                cursor = self._conn_info[connection_alias]['cursor']

                cursor.commit()

            except pyodbc.Error, err:
                logging.error(err)
                raise err

        else:
            
            raise Exception(stack()[0][3], \
                    "The type provided ('%s') is not valid.  No connection made" % connection_type)

    def list_values(self, connection_alias, connection_type,list_value):
        """
        commit the results from a previous command.  This is always used in conjunction
        with the execute_command() function, either implicitly or explicitly.

        :param connection_alias: the plain english name to associate with this connection
        :param connection_type: the type of connection to use
        :param list_value: the thing inside the database to list

        """

        logging.debug(" -- Working with connection '%s' of type '%s'" % (connection_alias, connection_type))

        if connection_type.lower() == 'odbc':

            if not self.is_connected(connection_alias) and list_value != 'sources':
                logging.debug(" --- The alias '%s' is not connected" % connection_alias)
                return

            try:

                logging.debug(" --- The list value is '%s'" % list_value)
                results = []

                if list_value == 'tables':

                    logging.debug(" -- Listing tables in '%s'" % connection_alias)
                    cursor = self._conn_info[connection_alias]['cursor']

                    for row in cursor.tables():
                        results.append(row)

                elif list_value == 'procedures':
                    logging.debug(" --- Listing procedures in '%s'" % connection_alias)
                    cursor = self._conn_info[connection_alias]['cursor']

                    for row in cursor.procedures():
                        results.append(row)

                elif list_value == 'sources':
                    logging.debug(" --- Listing sources in '%s'" % connection_alias)

                    for row in pyodbc.dataSources():
                        results.append(row)

                else:
            
                    raise Exception(stack()[0][3], "The list value provided ('%s') is not valid.  No connection made" % list_value)

                logging.debug(" --- Listing '%s'" % results)
                return results

            except pyodbc.Error, err:
                logging.error(err)
                raise err

        else:
            
            raise Exception(stack()[0][3], \
                    "The type provided ('%s') is not valid.  No connection made" % connection_type)

    @line_magic('db')
    def lmagic(self, line):
        """
            @argument('source', type=str, help='The identifier of the data source (optional)',default='', nargs='?')
            @argument('cmd', type=str, help='A command to be executed (optional)',default='', nargs='*')
            @argument('-src', '--source', help='The data source to use (optional).', action="store")
            @argument('-a', '--alias', help='The key to refer to this connection with', action="store")
            @argument('-def', '--default', help='The key to refer to this connection with', action="store")
            @argument('-c', '--connect', '--conn', help='Connect to this database', action="store_true")
            @argument('-d', '--disconnect', '--dis', help='Disconnect from this datbase', action="store_true")
            @argument('-t', '--type', help='Connection type (ODBC is the default)', action="store", default="odbc")
            @argument('-l', '--list', help='List things about the database.', action="store", nargs='?')
            @argument('-e', '--execute', '--exec', help='Some SQL to execute', action="store_true")
            @argument('-m', '--commit', help='Commit this transaction.', action="store_true")
            @argument('-r', '--rollback', help='Rollback this transaction.', action="store_true")
            @argument('-n', '--naked', help='Run a naked query (same as --connect --execute --fetch --disconnect)', action="store_true")
            @argument('--unsourced', help='Run an unsourced query (same as --connect --execute --fetch --disconnect)', action="store_true")
            @argument('-f', '--fetch', help='Fetch one or more records (default is all)', action="store", default=0,nargs='?')
            @argument('-u', '--uid', '--username', help='The user name to use (optional).', action="store", default='')
            @argument('-p', '--pwd', '--password', help='The password to use (optional).', action="store", default='')
            @argument('-h', '--help', help='Display help.', action="store_true")
            @argument('-v', '--verbose', help='Display debugging verbosely (same as --debug=DEBUG', action="store_true")
            @argument('--debug', help='Output debugging info', action="store", default='WARNING',nargs='?')
            @argument('-y', '--dry_run', '--dry', help='Make this a dry run', action="store_true")
            @argument('--explain', help='Give an explanation on exac', action="store_true")
            @argument('--note', help='Add a note for help with debugging', action="store", nargs="*")
            @argument('--cleanup', help='Clean up all the connections and shut down', action="store_true")
        """
        results = None
        #logging.getLogger().setLevel(logging.ERROR)

        logging.info(' - Starting parsing process')
        # parse the command line arguments and return the most important things:
        alias, key, cmd, fetch, args = self.parse_args(line)

        if args.explain or args.dry_run:
            self.explain(alias, key, cmd, fetch, args,line)

            if args.dry_run:
                return

        # The order of these commands are VERY important, as when a command is run
        # "naked" or "unsourced" it will scroll through these in order.  It is
        # critically imporant that you keep them in a logical order for database connections.

        if args.connect or args.naked:
            logging.info(' - Starting connection process')
            self.connect_to_source(alias,args.type, key, args.uid, args.pwd)

        if (args.execute or \
                args.naked or \
                args.unsourced) and \
                (len(cmd) > 0):

            logging.info(' - Starting execution process with "%s"' %cmd)
            self.execute_command(alias, args.type, cmd, fetch)

        if args.list is not None:
            logging.info(' - Starting list process')
            results = self.list_values(alias, args.type, args.list)

        if args.fetch == 'all' or args.fetch > 0 or args.naked or args.unsourced:

            logging.info('Starting fetch process')
            results = self.fetch(alias, args.type, fetch)
            logging.info(results)

        if args.commit or args.naked:
            logging.info(' - Starting commit process')
            self.commit(alias, args.type)

        if args.disconnect or args.naked:
            logging.info(' - Starting disconnect process')
            self.disconnect_from_source(alias, args.type)

        if not args.naked or args.unsourced:
            self._most_recent_conn_alias = alias

        if  args.cleanup:
            self.cleanup()

        if results is not None:
            logging.debug(' - Returning resultset')
            return results
        else:
            logging.debug(' - Returning nothing')
            return

        return line

    @cell_magic('db')
    def cmagic(self, line, cell):
        "my cell magic"
        #line = self.lmagic(line + ' ' + ''.join(cell).replace('\n', ' ').replace('\t',''))
        line = self.lmagic(line + ' ' + ''.join(cell).replace('\n', ' '))
        return line

    def cleanup(self):
        " shutting down all connections properly"

        logging.info("Closing all connections")

        shutdown_had_problems = False

        for alias in self._conn_info.keys():
            try:
                logging.debug("Closing %s" % alias)
                self.disconnect_from_source(alias,self._conn_info[alias]['type'])
            except err:
                logging.warning(" - There was a problem shutting down %s" % alias)
                shutdown_had_problems = True

            if shutdown_had_problems:
                raise Exception(stack()[0][3], \
                        "The list value provided ('%s') is not valid.  No connection made" % list_value)

            
    def __del__(self):
        self.cleanup()

    @line_magic
    def unload_ext(self, module_str):
        """Unload an IPython extension by its module name."""
        logging.info("Unloading extension")
        self.cleanup()
        self.shell.extension_manager.unload_extension(module_str)

# In order to actually use these magics, you must register them with a
# running IPython.  This code must be placed in a file that is loaded once
# IPython is up and running:
ip = get_ipython()
# You can register the class itself without instantiating it.  IPython will
# call the default constructor on it.
ip.register_magics(DbMagic)

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magics(DbMagic)
