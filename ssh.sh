args=("$@")
cmd=`loony -g rack:${args[0]} -l "%(facts:hostname)s" | sort`
for host in $cmd; do
	mySsh=`nmap $host -Pn -p ssh | grep open`
	if [[ $mySsh == *"22"* ]]
	then
		printf "$host works on SSH!\n"
	else
		printf "$host does NOT work on SSH!!!\n"
	fi
done;
