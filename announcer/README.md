#Announcer Guide

#To build run:
`$ make build`

#To run tests:
`$ make test`

##To re-sync a server's announcements for all path types run command:

**announcer --server sub-iad01-data01 --path_types prod_global,monitor,site_local,int_local**
**announcer -s sub-iad01-data01 -p prod_global,monitor,site_local,int_local**

##To re-sync an ASN on a server:

**announcer --server sub-iad01-data01 --asn 8835 --path_types prod_global,monitor**
**announcer -s sub-iad01-data01 -a 8835 -p prod_global,monitor**

##To re-sync an ASN on every PoP in a region:

**announcer --region eu --asn 3356 --path_types prod_global,monitor**
**announcer -r eu -a 3356 -p prod_global,monitor**

##To run announcer without actually updating billboard cloud:

**announcer --server sub-iad01-data01 --path_types monitor --dryrun**
**announcer -s sub-iad01-data01 -p monitor -d**

##To get a printout of the updates being pushed in billboard CLI format:

**announcer --server sub-iad01-data01 --path_types monitor --print**
**announcer -s sub-iad01-data01 -p monitor --print**

###This tool works with the policy YMLs in /veritas/neteng/policy:

`global.yml`
`regional.yml`
`pops.yml`

###along with netbox and billboard. Every ASN in billboard for a given PoP inherits any communities assigned
###to it in `pops.yml` and then is overlayed with any communities assigned to it in `regional.yml`, and then finally
###overlayed with any global communities in `global.yml`. Before an announcement for the specified path_type is
###generated, netbox is checked for tags like `ipv4-midgress-only` and `use-ipv4-int-local`. If a PoP is currently
###drained, then any announcements made by announcer will be pushed in a disabled state to prevent impact.

