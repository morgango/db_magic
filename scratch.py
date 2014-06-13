class DBMagicSource(object):

	def __init__(self, odbc_args):
		"""
		:param odbc_args: the arguments parsed from @magic_arguments
		:returns: formatted string
		"""
	
		pass
	
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

		pass
	
	def connect_to_source(self, connection_source, username=None, password=None):
		"""
		Establishes a connection to a data source and removes the alias.

		:param connection_source: the name of an an ODBC DSN or connection string
		:param username: the username to use for a connection (optional)
		:param password: connection_source: the password to use for a connection (optional)
		:returns: formatted string

		"""
		pass
	
	def disconnect_from_source(self):
		"""
		Disconnects a particular connection to a data source and removes the alias.

		"""

		pass
	
	def execute_command(self, command, fetch):
		"""
		Execute a command on a remote data source

		NOTE: this will not return a value, just execute the command.  Use fetch() 

		:param command:  the command to execute at the connection

		"""
	
		pass
	
	def fetch(self, fetch):
		"""
		Fetch the results from a previous command.  This is always used in conjunction
		with the execute_command() function, either implicitly or explicitly.

		:param fetch: how many records to fetch, either a positive integer or 'all'

		"""

		pass
	
	def commit(self):
		"""
		commit the results from a previous command.  This is always used in conjunction
		with the execute_command() function, either implicitly or explicitly.

		"""

		pass
	
	def list_values(self, list_value):
		"""
		commit the results from a previous command.  This is always used in conjunction
		with the execute_command() function, either implicitly or explicitly.

		:param list_value: the thing inside the database to list

		"""

		pass
	
	def cleanup(self):
		" shutting down all connections properly"
		
		pass
	
	def __del__(self):
		self.cleanup()

        
class ODBCSource(DBMagicSource):

	self._connection = None
	self._cursor = None
	self._is_connected = False

	
    def __init__self, odbc_args):
        """
        :param odbc_args: the arguments parsed from @magic_arguments
        :returns: formatted string
        """
        
        pass
        
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
        print("Args Parsed: %s" % args)
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
        
    def connect_to_source(self, connection_source, username=None, password=None):
        """
        Establishes a connection to a data source and removes the alias.

        :param connection_source: the name of an an ODBC DSN or connection string
        :param username: the username to use for a connection (optional)
        :param password: connection_source: the password to use for a connection (optional)
        :returns: formatted string

        """

		try:
			logging.debug("Attempting to connect")
			if (len(username) > 0 and len(password) > 0):
				self._connection = pyodbc.connect(connection_source,uid=username,pwd=password)
			else:
				self._connection = pyodbc.connect(connection_source)
			self._cursor = self._connection.cursor()
			self._is_connected = True
		except pyodbc.Error, err:
			logging.error(self._connection)
			logging.error(err[1])
			raise err
        
    def disconnect_from_source(self):
        """
        Disconnects a particular connection to a data source and removes the alias.

        """

		try:
			logging.debug("Attempting to disconnect")
			cursor = self._cursor.close()
			cnxn = self._connection.close()
			self._is_connected = False
		except pyodbc.Error, err:
			logging.error(err[1])
			raise err

		logging.debug("Disconnected data source")
			
    def execute_command(self, command, fetch):
        """
        Execute a command on a remote data source

        NOTE: this will not return a value, just execute the command.  Use fetch() 

        :param command:  the command to execute at the connection

        """
        
		if len(command) > 0:
			try:
				logging.debug("Attempting to execute '%s'" % command)
				self.__cursor.execute(command)
			except pyodbc.Error, err:
				logging.error(err[1])
				raise err
		else:
				logging.debug("Skipping empty command.")
        
    def fetch(self, fetch):
        """
        Fetch the results from a previous command.  This is always used in conjunction
        with the execute_command() function, either implicitly or explicitly.

        :param fetch: how many records to fetch, either a positive integer or 'all'

        """

		try:

			cursor = self._cursor
			description = []

			if (isinstance(fetch, str) or isinstance(fetch, unicode)) and 'all' in fetch:
				logging.debug("Running cursor.fetchall()")
				return cursor.fetchall()
			elif (long(fetch) == 0):
				logging.debug("Running cursor.fetchall()")
				return cursor.fetchall()
			elif long(fetch) > 0:
				logging.debug("Running cursor.fetchmany(%s)" % long(fetch))
				return cursor.fetchmany(long(fetch))
			else:
				logging.debug("'%s' is an invalid number of rows to fetch" % fetch)

		except pyodbc.ProgrammingError, err:
			logging.warning(err)
			pass
		except pyodbc.Error, err:
			logging.error(err)
			raise err
                        
    def commit(self):
        """
        commit the results from a previous command.  This is always used in conjunction
        with the execute_command() function, either implicitly or explicitly.

        """

		logging.debug("Commiting cursor")

		if not self.is_connected:
			logging.debug("The alias '%s' is not connected" % connection_alias)
			return
		try:
			self._cursor.commit()
		except pyodbc.Error, err:
			logging.error(err)
                        
    def list_values(self, list_value):
        """
        commit the results from a previous command.  This is always used in conjunction
        with the execute_command() function, either implicitly or explicitly.

        :param list_value: the thing inside the database to list

        """

		if not self._is_connected and list_value != 'sources':
			logging.debug("This object is not connected")
			return
		try:
			logging.debug("The list value is '%s'" % list_value)
			results = []
			if list_value == 'tables':
				logging.debug("Listing tables.)
				cursor = self._cursor
				for row in cursor.tables():
					results.append(row)
			elif list_value == 'procedures':
				logging.debug("Listing procedures.)
				cursor = self._conn_info[connection_alias]['cursor']
				for row in cursor.procedures():
					results.append(row)
			elif list_value == 'sources':
				logging.debug("Listing sources in")

				for row in pyodbc.dataSources():
					results.append(row)
			else:
				raise Exception(stack()[0][3], "The list value provided ('%s') is not valid.  No connection made" % list_value)

			return results
        
    def cleanup(self):
        " shutting down all connections properly"
            
        shutdown_had_problems = False

		try:
			logging.debug("Closing %s" % alias)
			self.disconnect_from_source()
		except err:
			logging.warning("There was a problem shutting down")
			shutdown_had_problems = True
		finally:
			if shutdown_had_problems:
				raise Exception(stack()[0][3], \
						"This object could not be shut down.")        
        
