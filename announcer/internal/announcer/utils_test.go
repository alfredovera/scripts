package announcer

import (
	"net"
	"reflect"
	"strings"
	"testing"
)

//Converts e.g. sub-iad01-data01 to IAD01 and hkg01-data01 to HKG01
func TestConvertServerToSiteID(t *testing.T) {
	server := "sub-iad01-data01"
	if len(server) == 12 {
		server = strings.ToUpper(server[0:5])
		if server != "IAD01" {
			t.Errorf("the server name isn't compatible")
		}
	} else if len(server) == 16 {
		server = strings.ToUpper(server[4:9])
		if server != "IAD01" {
			t.Errorf("the server name isn't compatible")
		}
	} else {
		t.Errorf("the server name isn't compatible")
	}
}

//For a given network, see if the host address belongs to the same subnet
func TestIsSameAddressFamily(t *testing.T) {
	hostAddress := "192.168.1.8/32"
	network := "192.168.1.0/24"
	_, cidr, err := net.ParseCIDR(network)
	if err != nil {
		t.Errorf("could not parse network")
	}
	pref, _, err := net.ParseCIDR(hostAddress)
	if err != nil {
		t.Errorf("could not parse host address")
	}
	if cidr.Contains(pref) != true {
		t.Errorf("the host address is not apart of the network address")
	}
}

// IsIPv4 checks if the string is an IP version 4.
func TestIsIPv4(t *testing.T) {
	str := "192.168.1.1"
	ip := net.ParseIP(str)
	if ip != nil && strings.Contains(str, ".") != true {
		t.Errorf("the address is not an IPv4 address")
	}
}

//Checks to see if we're comparing an IPv4 with IPv4 or IPv6 with IPv6
func TestV4tov6Check(t *testing.T) {
	ip1 := "192.168.1.1"
	ip2 := "172.16.16.1"
	var is1Ipv4, is2Ipv4 bool
	if strings.Contains(ip1, ".") {
		is1Ipv4 = true
	}
	if strings.Contains(ip2, ".") {
		is2Ipv4 = true
	}
	if is1Ipv4 != is2Ipv4 {
		t.Errorf("the two ip addresses are not in the same family")
	}
}

//Remove a string from a slice
func TestRemoveStringFromSliceIfExists(t *testing.T) {
	s := []string{"test1", "test2", "test3"}
	r := "test2"
	for i, v := range s {
		if v == r && i < len(s)-1 {
			result := append(s[:i], s[i+1:]...)
			if !reflect.DeepEqual(result, []string{"test1", "test3"}) {
				t.Errorf("string was not removed from slice")
			}
		} else if v == r && i == len(s)-1 {
			if reflect.DeepEqual(s[:i], []string{"test1", "test3"}) {
				t.Errorf("string was not removed from slice")
			}
		}
	}
}

//Takes a list communities and separates them with a comma and wraps quotes around it
func TestPrintCommunities(t *testing.T) {
	data := []string{"3660:2330", "2230:4566", "1225:234"}
	pathType := "monitor"
	if len(data) > 0 && pathType != siteLocal && pathType != intLocal {
		comm := strings.Join(data, ",")
		if `"`+comm+`"` != `"`+"3660:2330,2230:4566,1225:234"+`"` {
			t.Errorf("communities were not formatted correctly")
		}
	}
}

//Matches an IP address to an interface in netbox and checks for associated tags
func TestIsIpAddressTagged(t *testing.T) {
	passed := false
	ip := "32.141.173.1"
	server := "sub-mci01-data01"
	tagType := "midgress-only"
	ips, err := GetInterfaceTags(server, tagType)
	if err != nil {
		t.Errorf("could not get tag from netbox")
	}
	for _, v1 := range ips {
		for _, v2 := range v1 {
			ipAdd := ip + "/32"
			if IsSameAddressFamily(ipAdd, v2) {
				passed = true
			}
		}
	}
	if !passed {
		t.Errorf("could not match IP address with an interface in netbox that has the tag")
	}
}
