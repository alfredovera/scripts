package announcer

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"strings"
)

func getNetboxToken() (string, error) {
	token := os.ExpandEnv("$NETBOX_TOKEN")
	if token == noValue {
		return noValue, fmt.Errorf("could not find environment var NETBOX_TOKEN")
	}
	return token, nil
}

func MakeRequest(cmd string) (string, error) {
	req, err := http.NewRequest("GET", cmd, nil)
	if err != nil {
		return noValue, fmt.Errorf("http get request failed %v", err)
	}
	token, err := getNetboxToken()
	if err != nil {
		return noValue, fmt.Errorf("could not retrieve netbox token %v", err)
	}
	req.Header.Set("Authorization", "token "+token)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return noValue, fmt.Errorf("http client request failed %v", err)
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return noValue, fmt.Errorf("could not read http response %v", err)
	}
	bodyString := string(body)
	return bodyString, nil
}

func GetNetboxSites() (string, error) {
	result, err := MakeRequest(netboxURL + "dcim/sites")
	if err != nil {
		return noValue, fmt.Errorf("could not get netbox sites %v", err)
	}
	return result, nil
}

func GetRegions(region string) (Region, error) {
	reg := convertRegionCodeToNetboxRegion(region)
	cmd := netboxURL + netboxRegion + reg
	data, err := MakeRequest(cmd)
	if err != nil {
		return Region{}, fmt.Errorf("could not get netbox region data %v", err)
	}
	newRegion := Region{}
	err = json.Unmarshal([]byte(data), &newRegion)
	if err != nil {
		return Region{}, fmt.Errorf("could not unmarshal netbox region data %v", err)
	}
	return newRegion, nil
}

func GetNetboxDevice(server string) (Device, error) {
	cmd := netboxURL + netboxDevice + server
	data, err := MakeRequest(cmd)
	if err != nil {
		return Device{}, fmt.Errorf("could not get device from netbox %v", err)
	}
	var newDevice Device
	err = json.Unmarshal([]byte(data), &newDevice)
	if err != nil {
		return Device{}, fmt.Errorf("could not unmarshal netbox device data %v", err)
	}
	return newDevice, nil
}

func GetPrefixData(server string, cmd string) (Prefixes, error) {
	data, err := MakeRequest(cmd)
	if err != nil {
		return Prefixes{}, fmt.Errorf("could not get site_local from netbox %v", err)
	}
	var Prefixes Prefixes
	err = json.Unmarshal([]byte(data), &Prefixes)
	if err != nil {
		return Prefixes, fmt.Errorf("could not unmarshal netbox prefix data %v", err)
	}
	return Prefixes, nil
}

func GetAnycastPrefixes() ([]string, error) {
	var prefixList []string
	cmd := netboxURL + anycastAddresses
	data, err := MakeRequest(cmd)
	if err != nil {
		return prefixList, fmt.Errorf("no anycast prefixes were found in netbox %v", err)
	}
	var Prefixes Prefixes
	err = json.Unmarshal([]byte(data), &Prefixes)
	if err != nil {
		return prefixList, fmt.Errorf("could not unmarshal netbox prefix data %v", err)
	}
	for _, value := range Prefixes.Results {
		prefixList = append(prefixList, value.Prefix)
	}
	return prefixList, nil
}

func GetSiteLocals(server string) (string, string, error) {
	cmd := netboxURL + netboxPrefixes
	data, err := GetPrefixData(server, cmd)
	if err != nil {
		return noValue, noValue, fmt.Errorf("could not get site_local %v", err)
	}
	ip4, ip6 := parsePrefixDataForSiteLocal(data, server)
	return ip4, ip6, nil
}

func parsePrefixDataForSiteLocal(data Prefixes, server string) (string, string) {
	server = ConvertServerToSiteID(server)
	var err error
	stopCounter := 0
	var v4SiteLocal, v6SiteLocal string
	for len(data.Next) > 0 && stopCounter < 10 {
		for _, val := range data.Results {
			if strings.Contains(val.Description, server) && val.Role.Name == ipv4SiteLocal {
				v4SiteLocal = strings.ReplaceAll(val.Prefix, "/24", "")
			}
			if strings.Contains(val.Description, server) && val.Role.Name == ipv6SiteLocal {
				v6SiteLocal = strings.ReplaceAll(val.Prefix, "/48", "")
			}
		}
		stopCounter++
		data, err = GetPrefixData(server, strings.ReplaceAll(data.Next, "http", "https"))
		if err != nil {
			return noValue, noValue
		}
	}
	return v4SiteLocal, v6SiteLocal
}

func GetRegionOfServer(server string) (string, error) {
	var result string
	server = ConvertServerToSiteID(server)
	cmd := netboxURL + netboxSites + server
	data, err := MakeRequest(cmd)
	if err != nil {
		return noValue, fmt.Errorf("could not execute command for netbox region json %v", err)
	}
	newSite := Region{}
	err = json.Unmarshal([]byte(data), &newSite)
	if err != nil {
		return noValue, fmt.Errorf("could not unmarshal region data %v", err.Error())
	}
	for _, v := range newSite.Results {
		result = v.Region.Name
	}
	//Because the region names are different then what net-dev has defined, we need to convert them to net-dev/communities YML terminology
	return convertRegionCodeToYMLAbbrev(result), nil
}

//The 2-Character region codes used in the YMLs must be converted to the netbox Regions
func convertRegionCodeToNetboxRegion(region string) string {
	if region == "eu" {
		region = "europe"
	} else if region == "latam" {
		region = "latin-america-and-the-caribbean"
	} else if region == "na" {
		region = "northern-america"
	} else if region == "apac" {
		region = "asia"
	}
	return region
}

//The region names in Netbox must be converted to 2-Character region codes
func convertRegionCodeToYMLAbbrev(region string) string {
	if strings.Contains(region, "Europe") {
		region = "eu"
	} else if strings.Contains(region, "Latin") {
		region = "latam"
	} else if strings.Contains(region, "America") {
		region = "na"
	} else if strings.Contains(region, "Asia") {
		region = "apac"
	}
	return region
}

func matchInterfaceFromIPandIPList(ipList IPAddresses, ip string) (string, error) {
	for _, v := range ipList.Results {
		if IsSameAddressFamily(ip+"/128", v.Address) {
			return v.AssignedObject.Name, nil
		}
	}
	return noValue, fmt.Errorf("could not find interface for specified peer IP")
}

func extractIntLocalV6FromInterface(ipList IPAddresses, interfacePort string) string {
	for _, v := range ipList.Results {
		if v.AssignedObject.Name == interfacePort {
			if strings.Contains(v.Address, "/48") {
				return strings.ReplaceAll(v.Address, "1/48", noValue)
			}
		}
	}
	return noValue
}

func IsOldPrefixAdvertisement(server string, ip string, prefix string, linkType string) bool {
	if linkType != transitLink && IsIPv4(ip) {
		return false
	}
	_, interfacePort := GetInterfaceOfIP(server, ip, linkType)
	if interfacePort == noValue {
		return false
	}
	_, interfacePort2 := GetInterfaceOfIP(server, prefix, linkType)
	if interfacePort2 == noValue {
		return false
	}

	if interfacePort != interfacePort2 {
		return true
	}
	return false
}

func CheckForIPv6IntLocal(server string, ip string, linkType string) string {
	ips, interfacePort := GetInterfaceOfIP(server, ip, linkType)
	return extractIntLocalV6FromInterface(ips, interfacePort)
}

func GetInterfaceOfIP(server string, ip string, linkType string) (IPAddresses, string) {
	if linkType != transitLink && IsIPv4(ip) {
		return IPAddresses{}, noValue
	}
	ips, err := getListOfInterfaceIPsFromServer(server)
	if err != nil {
		return IPAddresses{}, noValue
	}
	interfacePort, err := matchInterfaceFromIPandIPList(ips, ip)
	if err != nil {
		return IPAddresses{}, noValue
	}
	return ips, interfacePort
}

func CheckForIPv4IntLocal(server string, ip string, linkType string, tags map[string]map[string][]string) string {
	if linkType != transitLink && IsIPv4(ip) {
		return noValue
	}
	tag := "use-slash-24-int-local"
	for _, intfaceValue := range tags {
		for _, tagValue := range intfaceValue {
			for _, ipValue := range tagValue {
				if strings.HasSuffix(ipValue, ".1/24") && IsIpAddressTagged(ip, server, tag, tags) {
					return strings.ReplaceAll(ipValue, ".1/24", ".0")
				}
			}
		}
	}
	return noValue
}

func GetInterfaceTags(server string) (map[string]map[string][]string, error) {
	tagMap := make(map[string]map[string][]string)
	cmd := netboxURL + netboxInterfaces + server + "&limit=2000"
	data, err := MakeRequest(cmd)
	if err != nil {
		return tagMap, fmt.Errorf("could not get interface data from netbox %v", err)
	}
	var newInterface Interface
	err = json.Unmarshal([]byte(data), &newInterface)
	if err != nil {
		return tagMap, fmt.Errorf("could not unmarshal netbox interface data %v", err)
	}
	tags := extractTagsFromServer(newInterface)
	ips, err := getListOfInterfaceIPsFromServer(server)
	if err != nil {
		return tagMap, fmt.Errorf("could not retrieve interface IPs from server %v", err)
	}
	for intfaceKey, intfaceValue := range tags {
		tempMap := make(map[string][]string)
		for _, tagValue := range intfaceValue {
			for _, ipAdd := range ips.Results {
				if intfaceKey == ipAdd.AssignedObject.Name {
					tempMap[tagValue] = append(tempMap[tagValue], ipAdd.Address)
				}
			}
		}
		tagMap[intfaceKey] = tempMap
	}
	return tagMap, nil
}

func getListOfInterfaceIPsFromServer(server string) (IPAddresses, error) {
	cmd := netboxURL + netboxIPAddressesOfDevice + server
	data, err := MakeRequest(cmd)
	if err != nil {
		return IPAddresses{}, fmt.Errorf("could not get netbox ip address information %v", err)
	}
	var newIPs IPAddresses
	err = json.Unmarshal([]byte(data), &newIPs)
	if err != nil {
		return IPAddresses{}, fmt.Errorf("could not unmarshal netbox ip address information %v", err)
	}
	return newIPs, nil
}

func extractTagsFromServer(iface Interface) map[string][]string {
	tags := make(map[string][]string)
	for _, result := range iface.Results {
		for _, tag := range result.Tags {
			if tag.Name != noValue {
				tags[result.Name] = append(tags[result.Name], tag.Slug)
			}
		}
	}
	return tags
}
