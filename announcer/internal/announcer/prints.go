package announcer

import (
	"fmt"
	"strings"
)

var (
	Info = Teal
	Warn = Yellow
	Fata = Red
)

var (
	Black   = Color("\033[1;30m%s\033[0m")
	Red     = Color("\033[1;31m%s\033[0m")
	Green   = Color("\033[1;32m%s\033[0m")
	Yellow  = Color("\033[1;33m%s\033[0m")
	Purple  = Color("\033[1;34m%s\033[0m")
	Magenta = Color("\033[1;35m%s\033[0m")
	Teal    = Color("\033[1;36m%s\033[0m")
	White   = Color("\033[1;37m%s\033[0m")
)

func Color(colorString string) func(...interface{}) string {
	sprint := func(args ...interface{}) string {
		return fmt.Sprintf(colorString,
			fmt.Sprint(args...))
	}
	return sprint
}

func printNewOrWithdrawnAnnouncements(announceType string) {
	output := noValue
	announcedOrWithdrawnPaths := newPaths
	if announceType == withdrawnKey {
		announcedOrWithdrawnPaths = withdrawnPaths
	}
	for PeerIP, manyPathParams := range announcedOrWithdrawnPaths.path {
		for _, pathParams := range manyPathParams {
			totalPaths++
			if announceType == announceKey {
				output += fmt.Sprintf("%-13s", Green("[ANNOUNCED] "))
			} else {
				output += fmt.Sprintf("%-13s", Teal("[WITHDRAWN] "))
			}
			output += fmt.Sprintf("%-18.17s", announcedOrWithdrawnPaths.server)
			output += fmt.Sprintf("%-12.11s", pathParams[keyName])
			output += fmt.Sprintf("%-7.6s", pathParams[keyAsn])
			output += fmt.Sprintf("%-20.19s", PeerIP)
			output += fmt.Sprintf("%-20.19s", (pathParams[keyPrefix] + "/" + pathParams[keyPrefixLength] + " "))
			output += fmt.Sprintf("%-12.11s", pathParams[keyType])
			output += fmt.Sprintf("%-10.9s", pathParams[keyState])
			output += "["
			output += fmt.Sprintf((pathParams[keyCommunities] + "]\n"))
		}
	}
	fmt.Print(output)
}

func modifyStateString(state string) string {
	if state == psEnabled {
		return enabled
	}
	if state == psDisabled {
		return disabled
	}
	return enabled
}

func createDiffLineParametersString() string {
	line := noValue
	for _, diffPaths := range missingPaths {
		totalPaths++
		line += Yellow("[CHANGED]   ")
		line += fmt.Sprintf("%-18.17s", diffPaths.Server)
		line += fmt.Sprintf("%-12.11s", diffPaths.Name)
		line += fmt.Sprintf("%-7.6s", diffPaths.ASN)
		line += fmt.Sprintf("%-20.19s", diffPaths.IP)
		line += fmt.Sprintf("%-20.19s", (diffPaths.Prefix + "/" + diffPaths.PrefixLength))
		line += fmt.Sprintf("%-12.11s", diffPaths.Type)
		line += fmt.Sprintf("%-10.9s", modifyStateString(diffPaths.State))
		line += "["
		line += combineAndColorizeCommunities(&diffPaths)
	}
	return line
}

func combineAndColorizeCommunities(diffPaths *BillboardDiff) string {
	line := noValue
	var communityString []string
	for index, community := range diffPaths.Diff.Communities {
		if comm, ok := diffPaths.Communities[community]; ok {
			if index < len(diffPaths.Diff.Communities)-1 {
				line += fmt.Sprintf(Green(comm) + ",")
			} else {
				line += Green(comm)
			}
			delete(diffPaths.Communities, comm)
		} else {
			if index < len(diffPaths.Diff.Communities)-1 {
				line += fmt.Sprintf(Red(community) + ",")
			} else {
				line += Red(community)
			}
		}
	}
	if len(diffPaths.Diff.Communities) > 0 && len(diffPaths.Communities) > 0 {
		line += ","
		for _, community := range diffPaths.Communities {
			communityString = append(communityString, community)
		}
	}
	line += strings.Join(communityString, ",")
	line += "]\n"
	return line
}

func printBillboardDiff() {
	output := noValue
	diffColumns := "%-18s%-12s%-7s%-20s%-20s%-12s%-10s%-1s\n"
	output += fmt.Sprintf("%-12s", "")
	output += fmt.Sprintf(diffColumns, "Server", "Provider", "ASN", "PeerIP", "Prefix", "Type", "State", "Communities")
	output += fmt.Sprintf("+%s+\n", strings.Repeat("-", 130))
	output += createDiffLineParametersString()
	fmt.Print(output)
}

//Generate a withdraw for bad advertisement
func printBillboardWithdraw(data *packagedBillboardParameters, paths ReceivedBillboardPaths) {
	fmt.Print("billboard withdraw " + generateBillboardCLIString(data, paths))
}

//Generate a printout for new announcements
func printBillboardAnnouncements(data *packagedBillboardParameters, prefix string, prefix_len string) {
	pathType := data.PathType
	fmt.Print("billboard announce ")
	fmt.Print(data.Server + " ")
	fmt.Print(data.PoPList.Ip + " ")
	fmt.Print("prefix=", prefix+" ")
	fmt.Print("prefix_len=", prefix_len+" ")
	fmt.Print("type=", pathType+" ")
	fmt.Print("state=", data.State+" ")
	fmt.Print("prepend_as=", fmt.Sprint(data.Prepend)+" ")
	fmt.Print(PrintCommunities(data.PoPList.Communities, pathType))
	fmt.Print("\n")
}

//Generate a printout for updating existing paths
func printBillboardUpdates(data *packagedBillboardParameters, paths ReceivedBillboardPaths) {
	fmt.Print("billboard update path " + generateBillboardCLIString(data, paths))
}

//Create the billboard command text
func generateBillboardCLIString(data *packagedBillboardParameters, paths ReceivedBillboardPaths) string {
	pathType := data.PathType
	cliString := ""
	cliString = cliString + data.Server + " "
	cliString = cliString + data.PoPList.Ip + " "
	cliString = cliString + "prefix=" + paths.Prefix + " "
	cliString = cliString + "prefix_len=" + fmt.Sprint(paths.PrefixLength) + " "
	cliString = cliString + "type=" + pathType + " "
	cliString = cliString + "state=" + data.State + " "
	cliString = cliString + "prepend_as=" + fmt.Sprint(data.Prepend) + " "
	cliString = cliString + PrintCommunities(data.PoPList.Communities, pathType)
	cliString = cliString + "\n"
	return cliString
}
