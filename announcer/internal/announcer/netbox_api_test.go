package announcer

import (
	"encoding/json"
	"io/ioutil"
	"net/http"
	"os"
	"reflect"
	"strings"
	"testing"
)

func TestGetNetboxToken(t *testing.T) {
	token := os.ExpandEnv("$NETBOX_TOKEN")
	if token == "" {
		t.Errorf("could not find token")
	}
}

func TestMakeRequest(t *testing.T) {
	cmd := "https://netbox.global.ftlprod.net/api/netboxRegiondcim/sites/?limit=5000&region=northern-america"
	req, err := http.NewRequest("GET", cmd, nil)
	if err != nil {
		t.Errorf("http get request failed %v", err)
	}
	token, err := getNetboxToken()
	if err != nil {
		t.Errorf("could not retrieve netbox token %v", err)
	}
	req.Header.Set("Authorization", "token "+token)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		t.Errorf("http client request failed %v", err)
	}
	defer resp.Body.Close()

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		t.Errorf("could not read http response %v", err)
	}
	if len(body) == 0 {
		t.Errorf("could not read http response %v", err)
	}
}

func TestGetNetboxSites(t *testing.T) {
	result, err := MakeRequest(netboxURL + "dcim/sites")
	if err != nil {
		t.Errorf("could not get netbox sites")
	}
	if len(result) == 0 {
		t.Errorf("could not get netbox sites")
	}
}

func TestGetRegions(t *testing.T) {
	cmd := "https://netbox.global.ftlprod.net/api/dcim/sites/?limit=5000&region=northern-america"
	data, err := MakeRequest(cmd)
	if err != nil {
		t.Errorf("could not get netbox region data %v", err)
	}
	newRegion := Region{}
	err = json.Unmarshal([]byte(data), &newRegion)
	if err != nil {
		t.Errorf("could not unmarshal netbox region data %v", err)
	}
}

func TestGetNetboxDevice(t *testing.T) {
	cmd := "https://netbox.global.ftlprod.net/api/dcim/devices/?limit=5000&name__ic=sub-mci01-data01"
	data, err := MakeRequest(cmd)
	if err != nil {
		t.Errorf("could not get device from netbox %v", err)
	}
	var newDevice Device
	err = json.Unmarshal([]byte(data), &newDevice)
	if err != nil {
		t.Errorf("could not unmarshal netbox device data %v", err)
	}
}

func TestGetPrefixData(t *testing.T) {
	cmd := "https://netbox.global.ftlprod.net/api/ipam/prefixes/?limit=1000"
	data, err := MakeRequest(cmd)
	if err != nil {
		t.Errorf("could not get site_local from netbox %v", err)
	}
	var Prefixes Prefixes
	err = json.Unmarshal([]byte(data), &Prefixes)
	if err != nil {
		t.Errorf("could not unmarshal netbox prefix data %v", err)
	}
}

func TestGetSiteLocals(t *testing.T) {
	cmd := "https://netbox.global.ftlprod.net/api/ipam/prefixes/?limit=1000"
	server := "sub-mci01-data01"
	data, err := GetPrefixData(server, cmd)
	if err != nil {
		t.Errorf("could not get site_local %v", err)
	}
	ip4, ip6 := parsePrefixDataForSiteLocal(data, server)
	if len(ip4) < 1 || len(ip6) < 1 {
		t.Errorf("could not parse prefix data")
	}
}

func TestParsePrefixDataForSiteLocal(t *testing.T) {
	cmd := "https://netbox.global.ftlprod.net/api/ipam/prefixes/?limit=1000"
	server := "sub-mci01-data01"
	data, err := GetPrefixData(server, cmd)
	if err != nil {
		t.Errorf("could not get site_local %v", err)
	}
	server = ConvertServerToSiteID(server)
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
			t.Errorf("could not get prefix data")
		}
	}
	if len(v4SiteLocal) < 1 || len(v6SiteLocal) < 1 {
		t.Errorf("could not get v4 site local or v6 site local")
	}
}

func TestGetRegionOfServer(t *testing.T) {
	server := "sub-mci01-data01"
	var result string
	server = ConvertServerToSiteID(server)
	cmd := netboxURL + netboxSites + server
	data, err := MakeRequest(cmd)
	if err != nil {
		t.Errorf("could not execute command for netbox region json %v", err)
	}
	newSite := Region{}
	err = json.Unmarshal([]byte(data), &newSite)
	if err != nil {
		t.Errorf("could not unmarshal region data %v", err.Error())
	}
	for _, v := range newSite.Results {
		result = v.Region.Name
	}
	//Because the region names are different then what net-dev has defined, we need to convert them to net-dev/communities YML terminology
	if convertRegionCodeToYMLAbbrev(result) != "na" {
		t.Errorf("could not get the region of server")
	}
}

//The 2-Character region codes used in the YMLs must be converted to the netbox Regions
func TestConvertRegionCodeToNetboxRegion(t *testing.T) {
	region := "eu"
	if region == "eu" {
		region = "europe"
	} else if region == "latam" {
		region = "latin-america-and-the-caribbean"
	} else if region == "na" {
		region = "northern-america"
	} else if region == "apac" {
		region = "asia"
	}
	if region == "eu" {
		t.Errorf("region code could not be converted to netbox name")
	}
}

//The region names in Netbox must be converted to 2-Character region codes
func TestConvertRegionCodeToYMLAbbrev(t *testing.T) {
	region := "Northern-Europe"
	if strings.Contains(region, "Europe") {
		region = "eu"
	} else if strings.Contains(region, "Latin") {
		region = "latam"
	} else if strings.Contains(region, "America") {
		region = "na"
	} else if strings.Contains(region, "Asia") {
		region = "apac"
	}
	if region == "Northern-Europe" {
		t.Errorf("region netbox name could not be converted to 2-character code")
	}
}

func TestMatchInterfaceFromIPandIPList(t *testing.T) {
	passed := false
	ip := "2001:1890:c03:d640::119a:6297"
	ipList, err := getListOfInterfaceIPsFromServer("sub-mci01-data01")
	if err != nil {
		t.Errorf("could not create list of IPs from netbox server")
	}
	for _, v := range ipList.Results {
		if IsSameAddressFamily(ip+"/128", v.Address) {
			passed = true
		}
	}
	if !passed {
		t.Errorf("could not match ip address to netbox server interface")
	}
}

func TestExtractIntLocalV6FromInterface(t *testing.T) {
	passed := false
	ipList, err := getListOfInterfaceIPsFromServer("sub-mci01-data01")
	if err != nil {
		t.Errorf("could not create list of IPs from netbox server")
	}
	interfacePort := "mcx4p1"
	for _, v := range ipList.Results {
		if v.AssignedObject.Name == interfacePort {
			if strings.Contains(v.Address, "/48") {
				passed = true
			}
		}
	}
	if !passed {
		t.Errorf("netbox interface did not have int_local assigned")
	}
}

func TestIsOldPrefixAdvertisement(t *testing.T) {
	server := "sub-mci01-data01"
	ip := "2600:370f:7022::1"
	prefix := "2600:370f:7027::1"
	linkType := "PRT_IPT_GLOBAL"
	if linkType != transitLink {
		t.Errorf("this is not a transit link")
	}
	_, interfacePort := GetInterfaceOfIP(server, ip, linkType)
	if interfacePort == "" {
		t.Errorf("did not find interface for IP")
	}
	_, interfacePort2 := GetInterfaceOfIP(server, prefix, linkType)
	if interfacePort2 == "" {
		t.Errorf("did not find interface for IP")
	}
	if interfacePort == interfacePort2 {
		t.Errorf("this is not an old advertisement, it's a valid advertisement")
	}
}

func TestCheckForIPv6IntLocal(t *testing.T) {
	server := "sub-mci01-data01"
	ip := "2001:1890:c03:d640::119a:6297"
	linkType := "PRT_IPT_GLOBAL"
	ips, interfacePort := GetInterfaceOfIP(server, ip, linkType)
	if !strings.Contains(extractIntLocalV6FromInterface(ips, interfacePort), ":") {
		t.Errorf("could not extract IPv6 int_local from server/ip")
	}
}

func TestGetInterfaceOfIP(t *testing.T) {
	server := "sub-mci01-data01"
	ip := "2600:370f:7027::1"
	linkType := "PRT_IPT_GLOBAL"
	if linkType != transitLink {
		t.Errorf("this is not a transit link")
	}
	ips, err := getListOfInterfaceIPsFromServer(server)
	if err != nil {
		t.Errorf("could not get a list of IPs from server")
	}
	interfacePort, err := matchInterfaceFromIPandIPList(ips, ip)
	if err != nil {
		t.Errorf("could not match IP with IPs in the list of server interfaces")
	}
	if len(interfacePort) < 1 {
		t.Errorf("no interface for IP match found")
	}
}

func TestCheckForIPv4IntLocal(t *testing.T) {
	passed := false
	server := "sub-cdg01-data01"
	ip := "193.251.250.83"
	linkType := "PRT_IPT_GLOBAL"
	if linkType != transitLink {
		t.Errorf("this link is not a transit connection")
	}
	tag := "use-slash-24-int-local"
	ips, err := GetInterfaceTags(server, tag)
	if err != nil {
		t.Errorf("could not retrieve tags from netbox interface")
	}
	for _, v := range ips {
		for _, v2 := range v {
			if strings.Contains(v2, ".1/24") && IsIpAddressTagged(ip, server, tag) {
				passed = true
			}
		}
	}
	if !passed {
		t.Errorf("did not find int_local for IPv4 address")
	}
}

func TestGetInterfaceTags(t *testing.T) {
	cmd := "https://netbox.global.ftlprod.net/api/dcim/interfaces/?device=sub-mci01-data01&limit=2000"
	server := "sub-cdg01-data01"
	tagType := "midgress-only"
	data, err := MakeRequest(cmd)
	if err != nil {
		t.Errorf("could not get interface data from netbox %v", err)
	}
	var newInterface Interface
	err = json.Unmarshal([]byte(data), &newInterface)
	if err != nil {
		t.Errorf("could not unmarshal netbox interface data %v", err)
	}
	tags := extractTagsFromServer(newInterface)
	ips, err := getInterfaceIPOfTaggedInterface(server, tags, tagType)
	if err != nil {
		t.Errorf("could not get netbox interface %v", err)
	}
	if len(ips) < 1 {
		t.Errorf("did not retrieve a valid list of ips")
	}
}

func TestGetListOfInterfaceIPsFromServer(t *testing.T) {
	cmd := "https://netbox.global.ftlprod.net/api/ipam/ip-addresses/?device=sub-mci01-data01"
	data, err := MakeRequest(cmd)
	if err != nil {
		t.Errorf("could not get netbox ip address information %v", err)
	}
	var newIPs IPAddresses
	err = json.Unmarshal([]byte(data), &newIPs)
	if err != nil {
		t.Errorf("could not unmarshal netbox ip address information %v", err)
	}
	if reflect.ValueOf(newIPs).IsNil() {
		t.Errorf("could not create a valid struct of IPAddresses")
	}
}
