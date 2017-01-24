# Creation Date:06-07-2016

# Variables
#############
rackSrc=racks		# File that contains the rack(s) to query
dump=dump.csv		# Where to dump all the unformatted info too
tmp=tmp.csv		# Temp file for more formatting shit
outFile=services.csv	# Where to dump all the formatted info too

# Core
#############

while read rack; do
	# Data format:
	# Rack, hostname, platform/augmentation, role, rack limit, contact email, contact team
	printf "Rack $rack\n"
	loony -D smf1 -g rack:$rack -l "%(groups:rack)s,%(facts:hostname)s,%(groups:platform)s,%(groups:role)s,%(attributes:service.racklimit)s,%(attributes:service.contact.email)s,%(attributes:service.team.eng)s" | sort | paste -sd " " >> $dump
	printf "\n"
done<$rackSrc
sed '/^$/d' $dump > $tmp			# Remove any blank lines from the file
cat $tmp | tr ' ' '\n' | tee $outFile		# The loony script adds the information in 1 line but seperates each host (and it's info) with spaces, replaces the spaces with new lines.
rm -rf {$dump, $tmp}				# Delete the $dump and $tmp files since they are no longer of use
