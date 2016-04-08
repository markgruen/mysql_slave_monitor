#!/bin/bash 
#emails="mgruenberg@test.com"
emails="mgruenberg@test.com,test1@test.com,test2@test.com"

send_email=0
force=0

USAGE="USAGE: $(basename $0) [-mf] [-h|-?]"

function printout
{
    echo "Date: ${date}"
    echo "Status: $status"
    echo "error level: $error_level"
    echo "$out"
}

function do_sendmail
{
    echo "$out" | mutt -s "[SLAVE $error_level] [$host]  ${date}" "$emails"
}

while getopts :mfh opt
do
    case $opt in
        m) send_email=1;;
        f) force=1;;
        ?|h) echo $USAGE
            exit;;
    esac
done

date="$(date "+%a %F %T")"
host="$(hostname | tr '[:lower:]' '[:upper:]')"
out=$(/home/mgruen/scripts/mysql_test_slave_status.py --verbose-pretty)
status=$?

#    Exit Codes:
#        0 all is okay
#        1 sql thread is dead
#        2 slave isnt running
#        3 behind
#        -1 error

error_level=""
case $status in
    1|2|-1) error_level="ERROR";;
    3) error_level="WARNING";;
    0) error_level="NORMAL"
esac

if [ $status -ne 0 -a $send_email -eq 1 ]; then
    printout
    do_sendmail
elif [ $force -eq 1 ]; then
    printout
    do_sendmail
else
    printout
fi
