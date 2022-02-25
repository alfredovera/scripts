package announcer

import (
	"bytes"
	"fmt"
	"net"
	"os/exec"
	"strings"
)

//For a given network, see if the host address belongs to the same subnet
func IsSameAddressFamily(hostAddress string, network string) bool {
	_, cidr, err := net.ParseCIDR(network)
	if err != nil {
		return false
	}
	pref, _, err := net.ParseCIDR(hostAddress)
	if err != nil {
		return false
	}

	return cidr.Contains(pref)
}

func areCommunitiesDifferent(comm1, comm2 []string) (bool, []string) {
	same1, difference1 := compareCommunityLists(comm1, comm2)
	same2, difference2 := compareCommunityLists(comm2, comm1)
	differences := append(difference1, difference2...)
	if same1 && same2 {
		return true, differences
	} else {
		return false, differences
	}
}

func compareCommunityLists(comm1, comm2 []string) (bool, []string) {
	commList1 := removeDuplicateCommunities(comm1)
	commList2 := removeDuplicateCommunities(comm2)
	comparisonMap := make(map[string]bool, len(commList2))
	for _, communityString := range commList2 {
		comparisonMap[communityString] = true
	}
	var diff []string
	for _, communityString := range commList1 {
		if _, found := comparisonMap[communityString]; !found {
			diff = append(diff, communityString)
		}
	}
	if len(diff) > 0 {
		return false, diff
	}
	return true, diff
}

func removeDuplicateCommunities(commList []string) []string {
	allKeys := make(map[string]bool)
	list := []string{}
	for _, item := range commList {
		if _, value := allKeys[item]; !value {
			allKeys[item] = true
			list = append(list, item)
		}
	}
	return list
}

//Splits a CIDR into a separate network and mask
func splitCIDRAddress(network string) (string, string) {
	if strings.Contains(network, "/") {
		tmpArray := strings.Split(network, "/")
		ip, mask := tmpArray[0], tmpArray[1]
		return ip, mask
	}
	return "", ""
}

// IsIPv4 checks if the string is an IP version 4.
func IsIPv4(str string) bool {
	ip := net.ParseIP(str)
	return ip != nil && strings.Contains(str, ".")
}

//Checks to see if we're comparing an IPv4 with IPv4 or IPv6 with IPv6
func V4tov6Check(ip1 string, ip2 string) bool {
	var is1Ipv4, is2Ipv4 bool
	if strings.Contains(ip1, ".") {
		is1Ipv4 = true
	}
	if strings.Contains(ip2, ".") {
		is2Ipv4 = true
	}
	if is1Ipv4 == is2Ipv4 {
		return true
	}
	return false
}

//Remove a string from a slice
func RemoveStringFromSliceIfExists(s []string, r string) []string {
	for i, v := range s {
		if v == r && i < len(s)-1 {
			return append(s[:i], s[i+1:]...)
		} else if v == r && i == len(s)-1 {
			return s[:i]
		}
	}
	return s
}

//Takes a list communities and separates them with a comma and wraps quotes around it
func PrintCommunities(data []string, pathType string) string {
	if len(data) > 0 && pathType != siteLocal && pathType != intLocal {
		comm := strings.Join(data, ",")
		return "communities=" + `"` + comm + `"`
	}
	return ""
}

//Grab the user's file path
func GetUsersGitRoot() (string, error) {
	cmd := exec.Command("git", "rev-parse", "--show-toplevel")
	var execOut bytes.Buffer
	var execErr bytes.Buffer
	cmd.Stdout = &execOut
	cmd.Stderr = &execErr
	err := cmd.Run()
	if err != nil {
		return "", fmt.Errorf("cannot Execute cmd %v", err)
	}
	outStr := execOut.String()
	return outStr, nil
}

//Converts e.g. sub-iad01-data01 to IAD01 and hkg01-data01 to HKG01
func ConvertServerToSiteID(server string) string {
	if len(server) == 12 {
		server = strings.ToUpper(server[0:5])
	} else if len(server) == 16 {
		server = strings.ToUpper(server[4:9])
	}
	return server
}

//Matches an IP address to an interface in netbox and checks for associated tags
func IsIpAddressTagged(ip string, server string, tagType string, tags map[string]map[string][]string) bool {
	for _, intfaceValue := range tags {
		for tagKey, tagValue := range intfaceValue {
			if tagType != tagKey {
				continue
			}
			for _, ipValue := range tagValue {
				ipAdd := ip + "/32"
				if IsSameAddressFamily(ipAdd, ipValue) {
					return true
				}
			}
		}
	}
	return false
}

func indent(line string, spacing int) string {
	indent := strings.Repeat(" ", spacing)
	return fmt.Sprintf("%s%s", indent, line)
}

func removeCommunitiesFromNonAnycastPrefixes(pathType string, communities []string) string {
	if pathType != monitor && pathType != prodGlobal {
		return noValue
	} else {
		return strings.Join(communities, ",")
	}
}

//Check if ip and pathType match an IPv6 site_local advertisement
func isV6ProdGlobal(ip string, pathType string) bool {
	return !IsIPv4(ip) && pathType == siteLocal
}
