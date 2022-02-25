package announcer

import (
	"fmt"
	"io/ioutil"
	"regexp"
	"strconv"
	"strings"

	"gitlab.ftlio.net/engineering/veritas/cli/infra/billboard/pkg/billboard"
	"gopkg.in/yaml.v3"
)

var (
	newPaths                                = AnnouncedOrWithdrawnPaths{}
	withdrawnPaths                          = AnnouncedOrWithdrawnPaths{}
	missingPaths                            = []BillboardDiff{}
	pathingInfo                             = make(map[string][]string)
	serverNameRegex          *regexp.Regexp = regexp.MustCompile(`^[A-Z]{3}[0-9]{2}$`)
	currentDrainedState                     = disabled
	defaultAnnouncementState                = disabled
	printMode                               = false
	testMode                                = false
	totalPaths                              = 0
)

type typePeerPathParams = map[string]string

//Creates a complete list of path types and their relevant prefix information
func addStandardAnnouncementPrefixes() {
	pathingInfo[keyPathTypes] = append(pathingInfo[keyPathTypes], []string{monitor, monitor, siteLocal, siteLocal, siteLocalv6, intLocal, intLocal}...)
	pathingInfo[keyPrefixes] = append(pathingInfo[keyPrefixes], []string{monitorPrefix1, monitorPrefix2, noValue, noValue, noValue, noValue, noValue}...)
	pathingInfo[keyPrefixLens] = append(pathingInfo[keyPrefixLens], []string{slash24, slash24, slash24, slash48, slash43, slash24, slash48}...)
	anycastList, err := GetAnycastPrefixes()
	if err != nil {
		return
	}
	for _, value := range anycastList {
		ip, mask := splitCIDRAddress(value)
		pathingInfo[keyPathTypes] = append(pathingInfo[keyPathTypes], prodGlobal)
		pathingInfo[keyPrefixes] = append(pathingInfo[keyPrefixes], ip)
		pathingInfo[keyPrefixLens] = append(pathingInfo[keyPrefixLens], mask)
	}
}

//Check to see if server in billboard is marked as DRAINED
func IsAgentDrained(server string) bool {
	data, err := billboard.GetAgents(billboardApiHost, billboardApiPort)
	if err != nil {
		return false
	}
	for _, v := range data.Agents {
		if v.Name == server && v.State.String() != drainedState {
			return false
		}
	}
	return true
}

//Reads a YML file for the specified file (e.g. Global, Region, PoP)
func readYaml(file string) ([]byte, error) {
	fileLocation, err := GetUsersGitRoot()
	if err != nil {
		return []byte{}, fmt.Errorf("could not grab users file location %v", err)
	}
	root := strings.TrimSuffix(fileLocation, "\n")
	filePath := fmt.Sprintf("%s%s", root, fmt.Sprintf("/neteng/policy/%s%s", file, ".yml"))
	return ioutil.ReadFile(filePath)
}

//Unmarshal the data for either a given region or a specific PoP
func getRegionalOrPoPData(file string) (regionalOrPoPData, error) {
	yamlFile, err := readYaml(file)
	if err != nil {
		return regionalOrPoPData{}, fmt.Errorf("region/pop yml could not be read %v", err)
	}
	data := regionalOrPoPData{}
	err = yaml.Unmarshal(yamlFile, data)
	if err != nil {
		return regionalOrPoPData{}, fmt.Errorf("region/pop yml could not be umarshalled %v", err)
	}
	return data, nil
}

//Unmarshal global.yml
func getGlobalData() (map[string]map[int]asnConfig, error) {
	yamlFile, err := readYaml(keyGlobal)
	if err != nil {
		return map[string]map[int]asnConfig{}, fmt.Errorf("could not read global yml %v", err)
	}
	data := globalData{}
	err = yaml.Unmarshal(yamlFile, data)
	if err != nil {
		return map[string]map[int]asnConfig{}, fmt.Errorf("could not unmarshal global yaml %v", err)
	}
	return data, nil
}

//Map the data for a given ASN in global.yml
func parseGlobalData(region string, asn string, file string) (globalComms map[int][]string, err error) {
	globalComms = make(map[int][]string)
	i, err := strconv.Atoi(asn)
	if err != nil {
		return map[int][]string{}, fmt.Errorf("could not read global yml %v", err)
	}
	globalYaml, err := getGlobalData()
	if err != nil {
		return map[int][]string{}, fmt.Errorf("could not read global yml %v", err)
	}
	if _, ok := globalYaml[keyGlobal][i]; ok {
		globalComms[i] = globalYaml[keyGlobal][i].Communities
	}
	return globalComms, nil
}

//Map parseGlobalData() and all regional data for an ASN and then combine them
func parseRegionalData(region string, asn string, file string) (map[int][]string, error) {
	globalBuild, err := parseGlobalData(keyGlobal, asn, file)
	if err != nil {
		return map[int][]string{}, fmt.Errorf("could not parse global data %v", err)
	}
	regionalYaml, err := getRegionalOrPoPData(file)
	if err != nil {
		return map[int][]string{}, fmt.Errorf("could not get regionalYAML %v", err)
	}
	combinedMap := make(map[int][]string)
	i, err := strconv.Atoi(asn)
	if err != nil {
		return map[int][]string{}, fmt.Errorf("could not convert asn to string %v", err)
	}
	combinedMap[i] = append(globalBuild[i], regionalYaml[keyRegion][region][i].Communities...)
	return combinedMap, nil
}

//For a given PoP extract all the ASN info and combine any regional/global data
func parsePoPData(server string, asn string, region string) (map[int][]string, error) {
	regionalAndGlobalBuild, err := parseRegionalData(region, asn, keyRegional)
	if err != nil {
		return map[int][]string{}, fmt.Errorf("could not parse regional data %v", err)
	}
	popYaml, err := getRegionalOrPoPData(keyPops)
	if err != nil {
		return map[int][]string{}, fmt.Errorf("could not gather popYaml %v", err)
	}
	combinedMap := make(map[int][]string)
	i, err := strconv.Atoi(asn)
	if err != nil {
		return map[int][]string{}, fmt.Errorf("could not convert asn to string %v", err.Error())
	}
	combinedMap[i] = append(popYaml[keyPops][server][i].Communities, regionalAndGlobalBuild[i]...)
	if popYaml[keyPops][server][i].RSPolicy {
		RSPolicyCommunities, err := getRSPolicyCommunities(popYaml[keyPops][server][i])
		if err != nil {
			return map[int][]string{}, fmt.Errorf("could not get RS policy communities %v", err)
		}
		combinedMap[i] = append(popYaml[keyPops][server][i].Communities, RSPolicyCommunities...)
	}
	return combinedMap, nil
}

//Find the PoP in pops.yml and return a mapping of all the data
func parseAllPoPData(server string) (map[int][]string, error) {
	combinedMaps := make(map[int][]string)
	popData, err := getRegionalOrPoPData(keyPops)
	if err != nil {
		return map[int][]string{}, fmt.Errorf("could not get pop data %v", err)
	}
	for k := range popData[keyPops] {
		if server == k {
			for k2 := range popData[keyPops][k] {
				combinedMaps[k2] = popData[keyPops][k][k2].Communities
				if popData[keyPops][k][k2].RSPolicy {
					policy, err := getRSPolicyCommunities(popData[keyPops][k][k2])
					if err != nil {
						return map[int][]string{}, fmt.Errorf("could not get RS policy communities %v", err)
					}
					combinedMaps[k2] = append(popData[keyPops][k][k2].Communities, policy...)
				}
			}
		}
	}
	return combinedMaps, nil
}

//Return a []string of the global route server communities - ASN 0000 represents the global route policy
func getRSPolicyCommunities(data asnConfig) ([]string, error) {
	global, err := getGlobalData()
	if err != nil {
		return []string{}, fmt.Errorf("could not get global yml %v", err)
	}
	tempComms := global[keyGlobal][0000].Communities
	globalComms := stripExcludeCommunities(tempComms, data)
	return globalComms, nil
}

//After having grabbed all the global communities, remove the ones tagged for exclusion
func stripExcludeCommunities(comms []string, data asnConfig) []string {
	for _, v := range data.RSExclude {
		comms = RemoveStringFromSliceIfExists(comms, v)
	}
	return comms
}

//This is combing all the communities associated with this PoP along with all Billboard Data
func makeServerMap(server string, communities map[int][]string) (map[string]ReceivedBillboard, error) {
	newBillboardMap := make(map[string]string)
	newBillboardMap[keyHostname] = server
	dummyPaths := ReceivedBillboardPaths{}
	dummyMap := ReceivedBillboard{}
	serverMap := make(map[string]ReceivedBillboard)
	result, err := billboard.GetPeers(newBillboardMap, billboardApiHost, billboardApiPort)
	if err != nil {
		return map[string]ReceivedBillboard{}, fmt.Errorf("could not get billboard peers %v", err)
	}
	for _, v := range result.Peers {
		dummyMap.Ip = v.Ip
		dummyMap.Name = v.Name
		dummyMap.Asn = v.As
		dummyMap.State = v.State.String()
		dummyMap.LinkType = v.Type.String()
		dummyMap.Paths = nil
		for _, y := range v.Paths {
			dummyPaths.Prefix = y.Prefix
			dummyPaths.PrefixLength = y.PrefixLen
			dummyPaths.Type = y.Type.String()
			dummyPaths.State = y.State.String()
			for _, community := range y.Communities {
				dummyPaths.CurrentCommunities = append(dummyPaths.CurrentCommunities, community.Value)
			}
			dummyMap.Paths = append(dummyMap.Paths, dummyPaths)
			dummyPaths.CurrentCommunities = nil
		}
		asn := int(dummyMap.Asn)
		if _, ok := communities[asn]; ok {
			dummyMap.Communities = communities[asn]
		}
		serverMap[v.Ip] = dummyMap
		dummyMap.Communities = nil
	}
	return serverMap, nil
}

//Out of the entire PoP Billboard Configuration, just extract the ASN that we're interested in
func extractOnlyAsnFromPoPData(mappings map[string]ReceivedBillboard, communities map[int][]string, asn string) map[string]ReceivedBillboard {
	commMapTrue := make(map[string]ReceivedBillboard)
	for k, v := range mappings {
		asnString := strconv.FormatUint(v.Asn, 10)
		if asn == asnString {
			commMap := ReceivedBillboard{}
			commMap.Asn = v.Asn
			commMap.Ip = v.Ip
			commMap.Name = v.Name
			commMap.LinkType = v.LinkType
			commMap.Paths = v.Paths
			commMap.State = v.State
			commMap.Communities = append(commMap.Communities, v.Communities...)
			commMapTrue[k] = commMap
		}
	}
	return commMapTrue
}

//Checks to see if any prepending needs to be added to billboard for the specified advertisement
func returnASPrepending(server string, asn int) int {
	popYaml, err := getRegionalOrPoPData(keyPops)
	if err != nil {
		return 0
	}
	return popYaml[keyPops][server][asn].PathPrepend
}

//Adds INT_LOCAL IPs to pathingInfo["prefixes"] for INT_LOCAL position if there is one
func assignIntLocalsForIP(server string, ip string, linkType string, tags map[string]map[string][]string) {
	intLocalV4Address := CheckForIPv4IntLocal(server, ip, linkType, tags)
	intLocalV6Address := CheckForIPv6IntLocal(server, ip, linkType)
	pathingInfo[keyPrefixes][5], pathingInfo[keyPrefixes][6] = intLocalV4Address, intLocalV6Address
}

//Assigns ipv4 and ipv6 site_locals for the input server
func assignSiteLocalsForServer(server string) (string, string, error) {
	v4SiteLocalAddress, v6SiteLocalAddress, err := GetSiteLocals(server)
	if err != nil {
		return "", "", fmt.Errorf("could not get site_locals from netbox %v", err)
	}
	pathingInfo[keyPrefixes][2], pathingInfo[keyPrefixes][3] = v4SiteLocalAddress, v6SiteLocalAddress
	return v4SiteLocalAddress, v6SiteLocalAddress, nil
}

//This takes the map[string]RecveivedBillboard of data which has all of the communities and current billboard advertisements,
//then based on pathType, deduces which paths are missing and which ones just need to be updated
func billboardAdvertisePoP(server string, pop map[string]ReceivedBillboard, pathType []string) error {
	v4SiteLocal, v6SiteLocal, err := assignSiteLocalsForServer(server)
	if err != nil {
		return fmt.Errorf("could not get site_locals from netbox %v", err)
	}
	tags, _ := GetInterfaceTags(server)

	if !IsAgentDrained(server) {
		currentDrainedState = enabled
	}
	for pathCount, path := range pathType {
		err := updateOrCreatePaths(server, pop, path, pathCount, v4SiteLocal, v6SiteLocal, tags)
		if err != nil {
			return fmt.Errorf("could not determine if the path is new %v", err)
		}
	}
	if printMode {
		fmt.Print("\n")
	}
	return nil
}

//Takes the peer info and asseses which paths need to be updated with communities and which ones need to be created
func updateOrCreatePaths(server string, pop map[string]ReceivedBillboard, pathType string, pathCount int, v4SiteLocal string, v6SiteLocal string, tags map[string]map[string][]string) error {
	// peerIpToManyPathParams example:
	// peerIpToManyPathParams["1.1.1.1"] = [
	// 	 {
	//     "prefix": "10.0.0.0", "prefix_len": "24", "type": "monitor", "state": "enabled"}
	//   }
	// ]
	peerIpToManyPathParams := map[string][]map[string]string{}

	for ip, ipArray := range pop {
		if pathType == intLocal {
			assignIntLocalsForIP(server, ip, ipArray.LinkType, tags)
		}
		billboardParams := packagedBillboardParameters{}
		billboardParams.CounterMap = make(map[string]bool)
		billboardParams.Tags = tags
		billboardParams.PeerIP = ip
		billboardParams.PoPData = pop
		billboardParams.PathType = pathType
		billboardParams.PathCount = pathCount
		billboardParams.Server = server
		billboardParams.PoPList = ipArray
		billboardParams.Prepend = returnASPrepending(server, int(pop[ip].Asn))
		billboardParams.State = currentDrainedState
		billboardParams.PeerState = ipArray.State
		billboardParams.ServerState = currentDrainedState
		billboardParams.NewAnnouncementsState = defaultAnnouncementState
		if IsIPv4(ip) {
			billboardParams.SiteLocal = v4SiteLocal
		} else {
			billboardParams.SiteLocal = v6SiteLocal
		}

		result, withdrawn, err := updateCurrentPaths(&billboardParams)
		if err != nil {
			return fmt.Errorf("could not update current paths %v", err)
		}
		withdrawnPaths.path[ip] = append(withdrawnPaths.path[ip], withdrawn...)
		withdrawnPaths.server = server

		peerIpToManyPathParams[ip] = append(peerIpToManyPathParams[ip], result...)

		missingPrefixes := getMissingPrefix(billboardParams.CounterMap, pathingInfo[keyPrefixes])
		result = renderMissingPaths(&billboardParams, missingPrefixes)
		newPaths.path[ip] = append(newPaths.path[ip], result...)
		newPaths.server = server
		peerIpToManyPathParams[ip] = append(peerIpToManyPathParams[ip], result...)
	}

	if !testMode {
		_, err := billboard.AnnouncePaths(server, peerIpToManyPathParams, billboardApiHost, billboardApiPort)
		if err != nil {
			return fmt.Errorf("could not announce paths to billboard cloud %v", err)
		}
	}
	return nil
}

//Loops through the peers in billboardData and updates all current paths with the proper communities
func updateCurrentPaths(data *packagedBillboardParameters) ([]typePeerPathParams, []typePeerPathParams, error) {
	var announcementPaths []typePeerPathParams
	var withdrawnPaths []typePeerPathParams
	for _, path := range data.PoPList.Paths {

		pathParams := typePeerPathParams{}

		currentPath := strings.ReplaceAll(path.Type, "PT_", "")
		currentPath = strings.ToLower(currentPath)
		if currentPath == data.PathType {
			data.CounterMap[path.Prefix] = true

			//We don't need to run this check on PNIs and IXPs
			if data.PoPList.LinkType == transitLink {

				if IsIpAddressTagged(data.PoPList.Ip, data.Server, netboxTagMidgressOnly, data.Tags) {
					if printMode {
						printBillboardWithdraw(data, path)
					}
					if !testMode {
						_, err := billboard.Withdraw(data.Server, data.PoPList.Ip, path.Prefix, int(path.PrefixLength), billboardApiHost, billboardApiPort)
						if err != nil {
							return []map[string]string{}, []map[string]string{}, fmt.Errorf("unable to withdraw bad route %v", err)
						}
					}

					withdrawnPaths = append(withdrawnPaths, addPathsToWithdrawnPaths(data, path))
					continue
				}
			}
			if IsOldPrefixAdvertisement(data.Server, data.PoPList.Ip, path.Prefix, data.PoPList.LinkType) {
				if printMode {
					printBillboardWithdraw(data, path)
				}
				if !testMode {
					_, err := billboard.Withdraw(data.Server, data.PoPList.Ip, path.Prefix, int(path.PrefixLength), billboardApiHost, billboardApiPort)
					if err != nil {
						return []map[string]string{}, []map[string]string{}, fmt.Errorf("unable to withdraw bad route %v", err)
					}
				}

				withdrawnPaths = append(withdrawnPaths, addPathsToWithdrawnPaths(data, path))
				continue
			}

			//We shouldn't have any communities on site_local and int_local path types
			if data.PathType == prodGlobal || data.PathType == monitor {
				if same, negativeDifference := areCommunitiesDifferent(path.CurrentCommunities, data.PoPList.Communities); !same {
					missingPaths = append(missingPaths, assignMissingPathValues(data, path, negativeDifference))

				}
			}

			pathParams[keyPrefix] = path.Prefix
			pathParams[keyPrefixLength] = strconv.FormatUint(uint64(path.PrefixLength), 10)
			pathParams[keyType] = data.PathType

			//Strip communities if it is not anycast
			if data.PathType != monitor && data.PathType != prodGlobal {
				pathParams[keyCommunities] = noValue
			} else {
				pathParams[keyCommunities] = strings.Join(data.PoPList.Communities, ",")
			}
			pathParams[keyPrepend] = strconv.Itoa(data.Prepend)

			announcementPaths = append(announcementPaths, pathParams)
			if printMode {
				printBillboardUpdates(data, path)
			}
		}
	}
	return announcementPaths, withdrawnPaths, nil
}

func addPathsToWithdrawnPaths(data *packagedBillboardParameters, path ReceivedBillboardPaths) map[string]string {
	pathParams := make(map[string]string)
	pathParams[keyName] = data.PoPList.Name
	pathParams[keyPrefix] = path.Prefix
	pathParams[keyPrefixLength] = strconv.FormatUint(uint64(path.PrefixLength), 10)
	pathParams[keyType] = data.PathType
	pathParams[keyCommunities] = strings.Join(data.PoPList.Communities, ",")
	pathParams[keyAsn] = strconv.FormatUint(data.PoPList.Asn, 10)
	pathParams[keyState] = modifyStateString(data.PeerState)
	return pathParams
}

func assignMissingPathValues(data *packagedBillboardParameters, path ReceivedBillboardPaths, removedComms []string) BillboardDiff {
	missingPathValues := BillboardDiff{}
	missingPathValues.Communities = make(map[string]string)
	missingPathValues.Server = data.Server
	missingPathValues.IP = data.PoPList.Ip
	missingPathValues.ASN = strconv.FormatUint(data.PoPList.Asn, 10)
	missingPathValues.Name = data.PoPList.Name
	missingPathValues.State = data.PoPList.State
	missingPathValues.Prefix = path.Prefix
	for _, community := range data.PoPList.Communities {
		missingPathValues.Communities[community] = community
	}
	missingPathValues.OldCommunities = path.CurrentCommunities
	missingPathValues.PrefixLength = strconv.FormatUint(uint64(path.PrefixLength), 10)
	missingPathValues.Type = data.PathType
	missingPathValues.Diff.Communities = removedComms
	return missingPathValues
}

//Takes a []string of missing prefixes for a peer and combines that with the Path information and communities
func renderMissingPaths(data *packagedBillboardParameters, prefixes []string) []typePeerPathParams {
	var announcementPaths []typePeerPathParams

	for y := 0; y < len(prefixes); y++ {

		for z := 0; z < len(pathingInfo[keyPrefixes]); z++ {
			pathParams := typePeerPathParams{}

			if isPrefixAValidNewAnnouncement(prefixes[y], pathingInfo[keyPrefixes][z], pathingInfo[keyPathTypes][z], data.PathType, data.PoPList.Ip) {

				//Do not need to run this check for PNIs and IXPs
				if data.PoPList.LinkType == transitLink {

					if IsIpAddressTagged(data.PoPList.Ip, data.Server, netboxTagMidgressOnly, data.Tags) {
						continue
					}
				}
				if len(pathingInfo[keyPrefixes][z]) != 0 {
					if isV6ProdGlobal(data.PoPList.Ip, pathingInfo[keyPathTypes][z]) {

						//If it matches on site_local /48, we want to produce a /43 advertisement as well
						pathParams[keyName] = data.PoPList.Name
						pathParams[keyPrefix] = pathingInfo[keyPrefixes][z]
						pathParams[keyAsn] = strconv.FormatUint(data.PoPList.Asn, 10)
						pathParams[keyPrefixLength] = pathingInfo[keyPrefixLens][z+1]
						pathParams[keyType] = data.PathType
						pathParams[keyCommunities] = strings.Join(data.PoPList.Communities, ",")
						pathParams[keyPrepend] = strconv.Itoa(data.Prepend)
						pathParams[keyState] = setAnnouncementState(data.PathType, data.State)
						announcementPaths = append(announcementPaths, pathParams)
						if printMode {
							printBillboardAnnouncements(data, pathingInfo[keyPrefixes][z], pathingInfo[keyPrefixLens][z+1])
						}
					}
					pathParams[keyName] = data.PoPList.Name
					pathParams[keyPrefix] = pathingInfo[keyPrefixes][z]
					pathParams[keyAsn] = strconv.FormatUint(data.PoPList.Asn, 10)
					pathParams[keyPrefixLength] = pathingInfo[keyPrefixLens][z]
					pathParams[keyType] = data.PathType
					pathParams[keyCommunities] = removeCommunitiesFromNonAnycastPrefixes(data.PathType, data.PoPList.Communities)
					pathParams[keyPrepend] = strconv.Itoa(data.Prepend)
					pathParams[keyState] = setAnnouncementState(data.PathType, data.State)
					announcementPaths = append(announcementPaths, pathParams)
					if printMode {
						printBillboardAnnouncements(data, pathingInfo[keyPrefixes][z], pathingInfo[keyPrefixLens][z])
					}
				}
			}
		}
	}
	return announcementPaths
}

//If its prod_global we are letting the user decide if it should be announced disabled or enabled
func setAnnouncementState(pathType string, popState string) string {
	if pathType == prodGlobal {

		//If the PoP is drained - we are overriding the users choice to announce disabled
		if popState != drainedState {
			return defaultAnnouncementState
		} else {
			return disabled
		}
	} else {
		return enabled
	}
}

//Only the IPs associated with the missing prefixes/pathTypes should be advertised
func isPrefixAValidNewAnnouncement(prefix string, pathPrefix string, pathType string, popPathType string, ip string) bool {
	if prefix == pathPrefix && prefix != noValue && pathType != siteLocalv6 {
		if pathType == popPathType {
			if V4tov6Check(ip, prefix) {
				return true
			}
		}
	}
	return false
}

//Take the PoP data and insert any related global/regional communities into the Asn.Communities struct for each peer
func overlayRegionalAndGlobalOnPoP(asns []map[int][]string, data map[string]ReceivedBillboard) map[string]ReceivedBillboard {
	for index, path := range data {
		tempData := data[index]
		for _, asnList := range asns {
			for asnNumber, asnCommunities := range asnList {
				if len(asnCommunities) != 0 {
					asnString := strconv.FormatUint(path.Asn, 10)
					if strconv.Itoa(asnNumber) == asnString {
						newMap := append(data[index].Communities, asnCommunities...)
						tempData.Communities = newMap
						data[index] = tempData
					}
				}
			}
		}
	}
	return data
}

//Take the Server name, figure out its region, then collect a []map[int][]string of all those regions ASNs
//communities if the server has a peer with that ASN
func gatherRegionalCommunitiesForServer(server string, asns map[string]string) ([]map[int][]string, error) {
	var asn []map[int][]string
	for k := range asns {
		reg, err := GetRegionOfServer(server)
		if err != nil {
			return []map[int][]string{}, fmt.Errorf("could not get Region of Server %v", err)
		}
		popAsn, err := parseRegionalData(reg, k, keyRegional)
		if err != nil {
			return []map[int][]string{}, fmt.Errorf("could not parse regional data %v", err)
		}
		if len(popAsn) != 0 {
			asn = append(asn, popAsn)
		}
	}
	return asn, nil
}

//Take all the communities from the billboard data for a server and format the data into a
//map[string]string to [typically] pass it into gatherRegionalCommunitiesForServer()
func findGlobalandRegionalCommunities(data map[string]ReceivedBillboard) map[string]string {
	associatedCommunities := make(map[string]string)
	for k := range data {
		asn := strconv.FormatUint(data[k].Asn, 10)
		if _, ok := associatedCommunities[asn]; !ok {
			associatedCommunities[asn] = asn
		}
	}
	return associatedCommunities
}

//For billboardAdvertisePoP() find out which paths are missing from the billboard data
//in relation to the pathType the user chose
func getMissingPrefix(counterMap map[string]bool, path []string) []string {
	var prefix []string
	for _, v := range path {
		if !counterMap[v] {
			prefix = append(prefix, v)
		}
	}
	return prefix
}

//For a given Server, find out which region its in, then collect all the servers in that same region
func findRegionalServersWithAsn(mappings map[int][]string, asn string, region string) ([]string, error) {
	billReq := make(map[string]string)
	var serverNames []string
	var serverList []string
	result, err := GetRegions(region)
	if err != nil {
		return []string{}, fmt.Errorf("could not get netbox region %v", err)
	}
	for _, v := range result.Results {
		if serverNameRegex.MatchString(v.Name) {
			hostname := "sub-" + strings.ToLower(v.Name) + "-data01"
			serverList = append(serverList, hostname)
		}
	}
	for _, v := range serverList {
		billReq[keyHostname] = v
		billReq[keyAsn] = asn
		val, err := billboard.GetPeers(billReq, billboardApiHost, billboardApiPort)
		if err != nil {
			return []string{}, fmt.Errorf("not able to get billboard peers %v", err)
		}
		if val != nil {
			serverNames = append(serverNames, v)
		}
	}
	return serverNames, nil
}

//Take all of the user inputs and formulate the data structures relevant to the options chosen and then execute
func CheckArgs(region string, asn string, server string, version bool, pathTypes []string, printTag bool, testTag bool, undrained bool) error {
	fmt.Println()
	if version {
		fmt.Println(announcerVersion)
		return nil
	}
	if len(pathTypes) > 0 {
		pathTypes = strings.Split(pathTypes[0], ",")
	} else {
		fmt.Println("\nerror: -p, --path_types is a mandatory attribute")
		return nil
	}
	if printTag {
		printMode = true
	}
	if testTag {
		testMode = true
	}
	if undrained {
		defaultAnnouncementState = enabled
	}
	newPaths.path = make(map[string][]map[string]string)
	withdrawnPaths.path = make(map[string][]map[string]string)
	addStandardAnnouncementPrefixes()
	if region != "" && asn != "" {
		regionalWithASNAnnouncements(region, asn, server, pathTypes)
	} else if asn != "" && server != "" {
		serverWithSpecificASNAnnouncements(region, asn, server, pathTypes)
	} else if server != "" {
		serverAnnouncements(region, asn, server, pathTypes)
	} else {

		//User has put in incorrect parameters
		return fmt.Errorf("the chosen parameters are not valid, read the --help for guidance")
	}
	printBillboardDiff()
	printNewOrWithdrawnAnnouncements(announceKey)
	printNewOrWithdrawnAnnouncements(withdrawnKey)
	fmt.Println()
	if testTag {
		fmt.Print("  ", totalPaths, " paths (would have been updated) [DRYRUN]\n")
	} else {
		fmt.Print("  ", totalPaths, " paths updated\n")
	}
	fmt.Print(indent("Announcements Complete\n", 2))
	return nil
}

//User has chosen e.g. --region eu --asn 3356
func regionalWithASNAnnouncements(region string, asn string, server string, pathTypes []string) error {
	data, err := parseRegionalData(region, asn, keyRegional)
	if err != nil {
		return fmt.Errorf("could not parse regional data %v", err)
	}
	servers, err := findRegionalServersWithAsn(data, asn, region)
	if err != nil {
		return fmt.Errorf("could not collect all regional servers with specified asn %v", err)
	}
	for _, server := range servers {
		data, err = parsePoPData(server, asn, region)
		if err != nil {
			return fmt.Errorf("could not parse pop data %v", err)
		}
		popData, err := makeServerMap(server, data)
		if err != nil {
			return fmt.Errorf("could not make server map %v", err)
		}
		asnData := extractOnlyAsnFromPoPData(popData, data, asn)
		if len(asnData) != 0 {
			billboardAdvertisePoP(server, asnData, pathTypes)
		}
	}
	return nil
}

//User has chosen e.g. --server sub-iad01-data01 --asn 3356
func serverWithSpecificASNAnnouncements(region string, asn string, server string, pathTypes []string) error {
	reg, err := GetRegionOfServer(server)
	if err != nil {
		return fmt.Errorf("could not get region of server %v", err)
	}
	data, err := parsePoPData(server, asn, reg)
	if err != nil {
		return fmt.Errorf("could not parse pop data %v", err)
	}
	popData, err := makeServerMap(server, data)
	if err != nil {
		return fmt.Errorf("could not make server map %v", err)
	}
	asnData := extractOnlyAsnFromPoPData(popData, data, asn)
	billboardAdvertisePoP(server, asnData, pathTypes)
	return nil
}

//User has chosen --server sub-iad01-data01 [To regenerate all PoP advertisements]
func serverAnnouncements(region string, asn string, server string, pathTypes []string) error {
	data, err := parseAllPoPData(server)
	if err != nil {
		return fmt.Errorf("could not parse all pop data %v", err)
	}
	popData, err := makeServerMap(server, data)
	if err != nil {
		return fmt.Errorf("could not make server map %v", err)
	}
	comms := findGlobalandRegionalCommunities(popData)
	commsList, err := gatherRegionalCommunitiesForServer(server, comms)
	if err != nil {
		return fmt.Errorf("could not gather regional communities for server %v", err)
	}
	overlayRegionalAndGlobalOnPoP(commsList, popData)
	billboardAdvertisePoP(server, popData, pathTypes)
	return nil
}
