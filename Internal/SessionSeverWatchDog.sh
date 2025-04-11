#!/bin/bash

LOG=GameSessionServer.log

if [ "$1" != "--nofork" ] ; then
    nohup "$0" --nofork $@ &>> $LOG &
    exit 0
fi

shift

cd "$(realpath "$(dirname "$0")/..")"

while true ; do
	python3 GameSessionServer.py --all-interfaces $@
	sleep 5
done
echo "$(date) : Watchdog finish" >> $LOG

exit 0
