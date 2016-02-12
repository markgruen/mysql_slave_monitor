#!/bin/bash 
#emails="mgruenberg@mdlive.com"
emails="mgruenberg@mdlive.com,dyoung@mdlive.com,cpastore@mdlive.com"

send_email=0

USAGE="USAGE: $(basename $0) [-m] [-h|-?]"

while getopts :mh opt
do
    case $opt in
        m) send_email=1;;
        ?|h) echo $USAGE
            exit;;
    esac
done

out=$(/home/mgruen/scripts/mysql_test_slave_status1.py --verbose-pretty)
status=$?

if [ $status -ne 0 ]; then
    if [ $status -eq 3 ]; then 
        error_level="WARNING"
    else
        error_level="ERROR"
    fi
    host="$(hostname | tr '[:lower:]' '[:upper:]')"
    #echo "[SLAVE $error_level] [$host]  $(date "+%Y-%m-%d %T")"
    echo "Date: $(date "+%Y-%m-%d %T")"
    echo "Status: $status"
    echo "error level: $error_level"
    echo "$out"
    if [ $send_email -eq 1 ]; then 
        echo "$out" | mutt -s "[SLAVE $error_level] [$host]  $(date "+%Y-%m-%d %T")" "$emails"
    fi
elif [ $send_email -eq 0 ]; then
    echo $(date "+%Y-%m-%d %T")
    echo $out
fi
