#! /usr/bin/env python
"""Slave Status/Monitor
    Usage: 
        mysql_slave_status.py [options]

    Options:
        -h, --help            Show this screen
        -v, --verbose         Verbose output 
        -V, --verbose-pretty  Pretty print output
        --version             Show version

    Exit Codes:
        0 all is okay
        1 sql thread is dead
        2 slave isn't running
        3 behind
        -1 error
"""

from __future__ import print_function
import json
import sys
import os
from datetime import datetime
import MySQLdb
from docopt import docopt

__version__ = '0.1.1'

'''
0 master
1 slave is broken
2 slave is running

select COUNT(1) SlaveThreads from information_schema.processlist where user = 'system user'
GRANT SELECT ON `performance_schema`.`threads` TO 'slavemon'@'localhost';
grant REPLICATION CLIENT on *.* to 'slavemon'@'localhost';
'''

def master_status(values):
    '''
    File
    Position
    Binlog_Do_DB
    Executed_Gtid_Set
    '''
    file, postion = (None,)*2
    try:
        file = values['File']
        position = values['Postion']
    except KeyError, e:
# this may mean not a master or no rows
        print(e)

def slave_status(values):
    (slave_running, seconds_behind, slave_running,slave_io_running,
    last_error_no, last_error, last_error_time, last_error_time_diff) = (None,)*8
    date = datetime.strftime(datetime.now(), '%Y/%m/%d %H:%M:%S')
    try:
        if values['Slave_IO_Running'] == 'Yes' and values['Slave_SQL_Running'] == 'Yes' :
            slave_running = 1
            slave_io_running = 1
            seconds_behind = int(values['Seconds_Behind_Master'])
        else:
            slave_running = 0
            slave_io_running = 1 if values['Slave_IO_Running'] == 'Yes' else 0
            last_error_no = values['Last_Errno']
            if last_error_no > 0L:
                last_error = values['Last_Error']
                last_error_time_str = values['Last_SQL_Error_Timestamp']
                last_error_time_diff = (datetime.now() - 
                        datetime.strptime(last_error_time_str,
                            '%y%m%d %H:%M:%S')).seconds
                last_error_time = datetime.strftime(
                        datetime.strptime(last_error_time_str, 
                            '%y%m%d %H:%M:%S'),
                        '%Y/%m/%d %H:%M:%S')
    except KeyError, e:
        print(e)
    return ((slave_running, slave_io_running, seconds_behind),
            (last_error_no,last_error,last_error_time,
             last_error_time_diff), date)


def pretty_print_status(status):
    if status[0][0:2] == (1,1):
        print('Slave is running and {0} seconds behind'.format(status[0][2]))
    elif status[0][0:2] == (0,0):
        print('Slave is not running')
    elif status[0][0:2] == (1,0) or status[1][0]>0L:
        print('Error No: {0}\n'.format(status[1][0]))
        print('{0}\n'.format(status[1][1]))
        print('Error occured at {0} and has been down for {1} seconds\n'.format(*status[1][2:]))


def calc_exit_status(status):
    ''' calculate exit status for shell exit 
        0 all is okay
        1 sql thread is dead
        2 slave isn't running
        3 behind
        -1 error
    '''
    assert isinstance(status, (tuple, long)), \
            'Bad status passed to calc_exit_status'

    if isinstance(status, tuple):
        if status[2] > cnf["max_seconds_behind"]:
            exit_status = 3
        elif status[1]==1 and status[0]==0:
            exit_status = 1
        elif status[1]==0 and status[0]==1:
            exit_status = 2
        elif status[1]==0 and status[0]==0:
            exit_status = 2
        else:
            exit_status = 0
    else:
        if status == 2:
            exit_status = 0
        elif status == 1:
            exit_status = 1
        else:
            exit_satus = 2
    return exit_status

def main(**args):
    global cnf
    user = os.environ['LOGNAME']
    if user == 'root':
        passwd_file = os.path.join('/', user, '.mysql_passwd')
    else:
        passwd_file = os.path.join('/home', user, '.mysql_passwd')
    with open(passwd_file) as data_file:    
        cnf = json.load(data_file)

    #host = cnf['host']
    try:
        db = MySQLdb.connect(host=cnf['host'],
                            user='slavemon',
                            passwd=cnf["passwords"]['slavemon'],
                            db='',
                            port=cnf['port']
                            )
    except KeyError, e:
        print("The key {0} doesn't exist in config file".format(str(e)))
        print("Exiting ...")
        sys.exit(-1)
    except Exception, e:
        print(e)
        sys.exit(-1)

    c = db.cursor()
    dc = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

    try:
        #n = c.execute("select COUNT(1) SlaveThreads from information_schema.processlist where user = 'system user'")
        n = c.execute("select count(*) from performance_schema.threads where name like 'thread/sql/slave%'")
        count_values = c.fetchone()
        n1 = dc.execute("show slave status")
        slave_values = dc.fetchone()
        n = dc.execute("show master status")
        master_values = dc.fetchone()
    except MySQLdb.Error, e:
        print('MySQL ERROR: {0}: {1}'.format(*e))
        if e[0] == 1142:
            print('You may need to grant select on performance_schema.threads to the user')
            print("   grant select on performance_schema.threads to {0}@'127.0.0.1'".format('slavemon'))
    else:
        status = slave_status(slave_values)
        exit_status = calc_exit_status(status[0])
        if args['--verbose']:
            print(status)
        elif args['--verbose-pretty']:
            pretty_print_status(status)
    dc.close()
    c.close()
    db.close()

    return exit_status, status[0][2]

if __name__ == '__main__':
    args = docopt(__doc__, version=__version__)
    exit_status, sec_behind = main(**args)
    if not(args['--verbose'] or args['--verbose-pretty']):
        print('Exiting Status: {0} Seconds Behind: {1}'.format(exit_status, sec_behind))
    sys.exit(exit_status)
    #print(arguments)
