args=("$@")
cmd=`loony -g rack:${args[0]} -l "%(facts:hostname)s" | sort`
for host in $cmd; do
	mySsh=`fping $host`
	if [[ $mySsh == *"unreachable"* ]]
	then
		printf "$host is BROKEN!\n"
	else
		printf "$host is WORKING!!!\n"
	fi
done;
