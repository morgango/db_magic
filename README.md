## Goals

The goal of the DBMagic project is to make iPython speak to data.

DBMagic will make iPython speak:
* Natively (in the language of the data)
* Fluently (with the same deft handling that comes with connections to [R](http://ipython.org/ipython-doc/dev/config/extensions/rmagic.html), [Ruby](http://nbviewer.ipython.org/github/minad/iruby/blob/master/IRuby-Example.ipynb), [Julia](http://nbviewer.ipython.org/github/JuliaLang/IJulia.jl/blob/master/python/doc/JuliaMagic.ipynb), and [many others](https://github.com/ipython/ipython/wiki/A-gallery-of-interesting-IPython-Notebooks)).
* Intelligently (in a way that makes sense with the data sources they are working with)

## Audience

The primary audience of DBmagic are people who work with data and with iPython notebook.  Typically this is a technical audience, but one that is less interested in code and more interested in getting things done and being able to share their code.

## Challenges

One of the primary challenges in doing Data Science and Engineering is that the tools are typically designed by computer scientist and software-oriented people.  They make great tools, but they don't always make sense for working with data.

For example, imagine a situatuation where you have a Terabyte of data sitting on a remote server inside a data store of some sort (SQL, NoSQL, Hadoop).  It would be silly for us to think that we should transfer all (or even some) of that data fom the remote server if we are trying to make an efficient, production-ready process.  Typically data transfer and I/O consumes 75% or more of the time it takes to complete a data-intensive process, and this is wasted time.

Python expects that you will either move data to the local machine to do work, or learn enough to use the computer-science based packages that provide remote access to machines (like [pyODBC](https://code.google.com/p/pyodbc/) or [JayDeBeeAPI](https://pypi.python.org/pypi/JayDeBeApi/).  If you are already a developer, then that isn't a bit deal.  However, often the people who know most about the data don't know (or don't care to learn) yet another programming language so they can manipulate their data.  They are interested in the data, not the tools, and all too often they would rather stick with difficult, archaic tools that they know rather than learn the newest thing.
 
The fundamental challenge is for iPython to speak to the data in the right place, with the right langage, at the right time.  DBMagic is all about doing just that.

## Design

The primary design goal of DBmagic is to make it possible to retrieve data with the simplest possible syntax and without requiring knowledge of the underlying python packages.

Instead of having code that looks like:

    import pyodbc

    # Information on where the data actually resides
    demo_db="MY_DB"

    # ODBC Connection Information
    dsn = "MY_SRC"
    pw = "LbhCrrxrqFarnxlUnpxre".encode('rot13')
    odbc_connection_string = 'DSN=%s;PWD=%s;DB=%s' % (dsn, pw, demo_db ) 

    cnxn = pyodbc.connect(odbc_connection_string)
    cursor = cnxn.cursor()

    for row in cursor.tables():
        print row.table_name

I believe that people who work with data would rather write code that
looks like:

    %db SELECT * FROM my_table 

or 

    %%db MY_DB

    SELECT
        *
    FROM
        my_table

### Comparisons

I have seen similar projects to this one, including [iPython-SQL](https://github.com/catherinedevlin/ipython-sql) and [Query](https://github.com/boydgreenfield/query).  Both of these are great tools and the authors have done excellent work.  You absolutely should check them out and see if they work better for your needs. %sql was an inspiration in writing this package, I only discovered query after I was in QA for this package but it looks really interesting.

I am building DBMagic from the perspective of dealing with big, heterogeneous data sources that requires the ability to issue native, well supported commands.  

I looked at both of these tools and found that in my own work, I would be limited by:

- The platforms that I need to access (SQLAlchemy doesn't seem to have native dialects for Netezza, Teradata, Hive, Impala, AsterData, Elasticsearch, Hbase, etc.) 
- The way that I write my code (I don't want to write Python to get to data unless it helps me somehow)
- The way that I access the data (an Hbase or Elasticsearch query looks and behaves nothing like SQL)

Honestly, I thought it would be more fun to write this package rather than to write SQLAlchemy dialects, so I did this.

## Supported Platforms

### Client Platforms

DBMagic should be able to run on any platform that supports iPython and the underlying packages that it utilizes (ODBC and JDBC).  This has been tested on Mac OS X and Windows.

### Connection Protocols

DBMagic currently supports ODBC database connections.  This was chosen because it is a widely-used format with a lot of flexibility and connection options. The downside (and it is well understood) is that that ODBC is harder to use for non-Windows platforms (although I developed this completely on a Mac).

See the roadmap section for more details on expansion.

## Installation and Loading

In your iPython window, run the command:

    %install_ext https://raw.githubusercontent.com/morgango/db_magic/master/db.py

You can then load the library with the command:

    %load_ext db

You should be able to run a simple command, like:

    %db --list sources

I have seen it where you need to restart the kernel after installing the extension and/or pyODBC.

## Requirements

DBMagic requires the [pyODBC](https://code.google.com/p/pyodbc/) package for access to ODBC databases.  You should be able to install it from the command line with:

    pip install pyodbc

If you are running on the Windows platform, you may need to install the [pyODBC binary](https://code.google.com/p/pyodbc/downloads/list) appropriate to the O/S that you are running.

## Documentation

There are several options for documentation.

1. There is internal documentation within iPython using `?%db` option.
1. There is a [quickstart](http://nbviewer.ipython.org/github/morgango/db_magic/blob/master/db_magic_quickstart.ipynb) available that gets you started as quickly as possible. 
1. There is a lengthy [tutorial](http://nbviewer.ipython.org/github/morgango/db_magic/blob/master/db_magic_cookbook.ipynb) available that walks through how to use the library in a very detailed way.
1. There is a [troubleshooting guide](http://nbviewer.ipython.org/github/morgango/db_magic/blob/master/db_magic_troubleshooting.ipynb) available that walks through how to use the library in a very detailed way.
1. The [unit tests](http://nbviewer.ipython.org/github/morgango/db_magic/blob/master/db_magic_odbc_unit_tests.ipynb) are available as an iPython notebook, you can see exactly how I use the code myself.


## Roadmap
The strategy for picking platforms to support follows the [Pareto Principle](http://en.wikipedia.org/wiki/Pareto_principle). We are going to go with what is most popular first, then add in support for niche-platforms on an as-needed basis.

### Connection Protocols
In the near-term roadmap we will be adding support for JDBC. This is another widely popular protocol that is more native to the \*NIX platform and has a lot of free drivers available.  In addition, JDBC is gaining support for non-relational databases (such as [Hive](https://cwiki.apache.org/confluence/display/Hive/HiveJDBCInterface), [Impala](http://www.cloudera.com/content/cloudera/en/products-and-services/cdh/impala.html), [HBase](http://www.hbql.com/examples/jdbc.html), and [Neo4j](http://www.neo4j.org/develop/tools/jdbc)).  I will need to do some work to make this happen, but it shouldn't be too different from the initial ODBC release.

Between ODBC and JDBC, we will be covering a wide swath of the database landscape.  After that, I hope to make the underlying library modular enough that it would be easy to add support without having to modify the underlying source code too much. Definitely not there yet.

### NoSQL Databases

I will be adding support for NoSQL databases at some point in the future. By market share, it seems like [MongoDB](http://mongodb.com) and [Cassandra](http://cassandra.apache.org) would be the place to start. No promises here.

I really like [Elasticsearch](http://elasticsearch.org) and would be inclined to build something for it simply out of personal preference. This would be something good to do after the library is modular enough. 

## Testing

There are unit tests available [here](http://nbviewer.ipython.org/github/morgango/db_magic/blob/master/odbc_unit_tests.ipynb).  These are all in an iPython notebook, using [iPython Nose](http://nbviewer.ipython.org/github/swcarpentry/2012-11-scripps/blob/master/python/testing-with-nose.ipynb).
