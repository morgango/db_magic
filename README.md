## Goals

The goal of the DBMagic project is to make iPython talk to data.

DBMagic will make iPython speak:
* Natively (in the language of the data)
* Fluently (with the same deft handling that comes with connections to [R](http://ipython.org/ipython-doc/dev/config/extensions/rmagic.html), [Ruby](http://nbviewer.ipython.org/github/minad/iruby/blob/master/IRuby-Example.ipynb), [Julia](http://nbviewer.ipython.org/github/JuliaLang/IJulia.jl/blob/master/python/doc/JuliaMagic.ipynb), and [many others](https://github.com/ipython/ipython/wiki/A-gallery-of-interesting-IPython-Notebooks)).
* Intelligently (in a way that makes sense with the data sources they are working with)

## Audience

The primary audience of **`DBmagic`** are people who work with data and with iPython notebook.  Typically this is a technical audience, but one that is less interested in code and more interested in getting things done and being able to share their code.

## Challenges

One of the primary challenges in doing Data Science and Engineering is that the tools are typically designed by computer scientist and software-oriented people.  They make great tools, but they don't always make sense for working with data.

For example, imagine a situatuation where you have a Terabyte of data sitting on a remote server inside a data store of some sort (SQL, NoSQL, Hadoop).  It would be silly for us to think that we should transfer all (or even some) of that data fom the remote server if we are trying to make an efficient, production-ready process.  Typically data transfer and I/O consumes 75% or more of the time it takes to complete a data-intensive process, and this is wasted time.

At the same time, often the people who know most about the data don't know (or don't care to learn) yet another programming language so they can manipulate their data.  They are interested in the data, not the tools, and all too often they would rather stick with difficult, archaic tools that they know rather than learn the newest thing.
 
## Supported Platforms

DBMagic currently supports ODBC database connections.  This was chosen because it is a widely-used format with a lot of flexibility and connection options. The downside (and it is well understood) is that that ODBC is harder to use for non-Windows platforms (although I developed this completely on a Mac).

See the roadmap section for more details on expansion.

## Design

The primary design goal of **`DBmagic`** is to make it possible to retrieve data with the simplest possible syntax and without requiring knowledge of the underlying python packages.

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

## Documentation

There are several options for documentation.

1. There is internal documentation within iPython using `?%db` option.
1. There is a lengthy [tutorial](https://github.com/morgango/db_magic/blob/master/odbc_unit_tests.ipynb) available that walks through how to use the library in a very detailed way.
1. The [unit tests](https://github.com/morgango/db_magic/blob/master/odbc_unit_tests.ipynb) are available as an iPython notebook, you can see exactly how I use the code myself.


## Roadmap
The strategy for picking platforms to support follows the [Pareto Principle](http://en.wikipedia.org/wiki/Pareto_principle). We are going to go with what is most popular first, then add in support for niche-platforms on an as-needed basis.

In the near-term roadmap we will be adding support for JDBC. This is another widely popular protocol that is more native to the \*NIX platform and has a lot of free drivers available.  In addition, JDBC is gaining support for non-relational databases (such as [Hive](https://cwiki.apache.org/confluence/display/Hive/HiveJDBCInterface), [Impala](http://www.cloudera.com/content/cloudera/en/products-and-services/cdh/impala.html), [HBase](http://www.hbql.com/examples/jdbc.html), and [Neo4j](http://www.neo4j.org/develop/tools/jdbc)).  I will need to do some work to make this happen, but it shouldn't be too different from the initial ODBC release.

Between ODBC and JDBC, we will be covering a wide swath of the database landscape.  After that, I hope to make the underlying library modular enough that it would be easy to add support without having to modify the underlying source code too much. Definitely not there yet.

### NoSQL Databases

I will be adding support for NoSQL databases at some point in the future. By market share, it seems like [MongoDB](http://mongodb.com) and [Cassandra](http://cassandra.apache.org) would be the place to start. No promises here.

I really like [Elasticsearch](http://elasticsearch.org) and would be inclined to build something for it simply out of personal preference. This would be something good to do after the library is modular enough. 

## Testing

There are unit tests available [here](http://nbviewer.ipython.org/github/morgango/db_magic/blob/master/odbc_unit_tests.ipynb).  These are all in an iPython notebook, using [iPython Nose](http://nbviewer.ipython.org/github/swcarpentry/2012-11-scripps/blob/master/python/testing-with-nose.ipynb).


======
