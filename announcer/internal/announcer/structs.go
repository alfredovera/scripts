package announcer

type AnnouncedOrWithdrawnPaths struct {
	path   map[string][]map[string]string
	server string
}

type BillboardDiff struct {
	Server         string
	Name           string
	ASN            string
	IP             string
	State          string
	Prefix         string
	PrefixLength   string
	Type           string
	OldCommunities []string
	Communities    map[string]string
	Diff           struct {
		Communities []string
	}
}

type ReceivedBillboardPaths struct {
	PrefixLength       uint32
	Prefix             string
	Type               string
	State              string
	CurrentCommunities []string
}

type ReceivedBillboard struct {
	Asn         uint64
	Name        string
	Ip          string
	State       string
	LinkType    string
	Communities []string
	Paths       []ReceivedBillboardPaths
}

type asnConfig struct {
	PathPrepend int      `yaml:"as_prepend"`
	RSPolicy    bool     `yaml:"rs_policy"`
	Name        string   `yaml:"name"`
	VendorLink  string   `yaml:"vendor_link"`
	RSExclude   []string `yaml:"rs_exclude"`
	Communities []string `yaml:"communities"`
}

type packagedBillboardParameters struct {
	Prepend               int
	PathCount             int
	PeerState             string
	ServerState           string
	State                 string
	PeerIP                string
	Server                string
	SiteLocal             string
	NewAnnouncementsState string
	PathType              string
	CounterMap            map[string]bool
	PoPList               ReceivedBillboard
	PoPData               map[string]ReceivedBillboard
	Tags                  map[string]map[string][]string
}

type globalData map[string]map[int]asnConfig

type regionalOrPoPData map[string]map[string]map[int]asnConfig
