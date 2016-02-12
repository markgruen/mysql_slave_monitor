create user slavemon@'127.0.0.1' identified by 'secretPassword';
GRANT REPLICATION CLIENT ON *.* TO 'slavemon'@'127.0.0.1';
GRANT SELECT ON `performance_schema`.`threads` TO 'slavemon'@'127.0.0.1';

show grants for slavemon@'127.0.0.1';

# show an example crontab entry
select "0,30 * * * *    /home/mgruen/scripts/check_slave.sh -m > /home/mgruen/chk.log" as "add crontab entry";

