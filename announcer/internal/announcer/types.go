package announcer

import (
	"time"
)

type Region struct {
	Count    int         `json:"count"`
	Next     string      `json:"next"`
	Previous interface{} `json:"previous"`
	Results  []struct {
		ID     int    `json:"id"`
		URL    string `json:"url"`
		Name   string `json:"name"`
		Slug   string `json:"slug"`
		Status struct {
			Value string `json:"value"`
			Label string `json:"label"`
		} `json:"status"`
		Region struct {
			ID    int    `json:"id"`
			URL   string `json:"url"`
			Name  string `json:"name"`
			Slug  string `json:"slug"`
			Depth int    `json:"_depth"`
		} `json:"region"`
		Tenant          interface{} `json:"tenant"`
		Facility        string      `json:"facility"`
		Asn             int         `json:"asn"`
		TimeZone        interface{} `json:"time_zone"`
		Description     string      `json:"description"`
		PhysicalAddress string      `json:"physical_address"`
		ShippingAddress string      `json:"shipping_address"`
		Latitude        string      `json:"latitude"`
		Longitude       string      `json:"longitude"`
		ContactName     string      `json:"contact_name"`
		ContactPhone    string      `json:"contact_phone"`
		ContactEmail    string      `json:"contact_email"`
		Comments        string      `json:"comments"`
		Tags            []struct {
			ID    int    `json:"id"`
			URL   string `json:"url"`
			Name  string `json:"name"`
			Slug  string `json:"slug"`
			Color string `json:"color"`
		} `json:"tags"`
		CustomFields struct {
			CountryCode         string `json:"country_code"`
			D42ID               int    `json:"d42_id"`
			PeeringdbFacilityID string `json:"peeringdb-facility-id"`
		} `json:"custom_fields"`
		Created             string    `json:"created"`
		LastUpdated         time.Time `json:"last_updated"`
		CircuitCount        int       `json:"circuit_count"`
		DeviceCount         int       `json:"device_count"`
		PrefixCount         int       `json:"prefix_count"`
		RackCount           int       `json:"rack_count"`
		VirtualmachineCount int       `json:"virtualmachine_count"`
		VlanCount           int       `json:"vlan_count"`
	} `json:"results"`
}

type Device struct {
	Count    int         `json:"count"`
	Next     interface{} `json:"next"`
	Previous interface{} `json:"previous"`
	Results  []struct {
		ID          int    `json:"id"`
		URL         string `json:"url"`
		Name        string `json:"name"`
		DisplayName string `json:"display_name"`
		DeviceType  struct {
			ID           int    `json:"id"`
			URL          string `json:"url"`
			Manufacturer struct {
				ID   int    `json:"id"`
				URL  string `json:"url"`
				Name string `json:"name"`
				Slug string `json:"slug"`
			} `json:"manufacturer"`
			Model       string `json:"model"`
			Slug        string `json:"slug"`
			DisplayName string `json:"display_name"`
		} `json:"device_type"`
		DeviceRole struct {
			ID   int    `json:"id"`
			URL  string `json:"url"`
			Name string `json:"name"`
			Slug string `json:"slug"`
		} `json:"device_role"`
		Tenant   interface{} `json:"tenant"`
		Platform interface{} `json:"platform"`
		Serial   string      `json:"serial"`
		AssetTag interface{} `json:"asset_tag"`
		Site     struct {
			ID   int    `json:"id"`
			URL  string `json:"url"`
			Name string `json:"name"`
			Slug string `json:"slug"`
		} `json:"site"`
		Rack         interface{} `json:"rack"`
		Position     interface{} `json:"position"`
		Face         interface{} `json:"face"`
		ParentDevice interface{} `json:"parent_device"`
		Status       struct {
			Value string `json:"value"`
			Label string `json:"label"`
		} `json:"status"`
		PrimaryIP        interface{} `json:"primary_ip"`
		PrimaryIP4       interface{} `json:"primary_ip4"`
		PrimaryIP6       interface{} `json:"primary_ip6"`
		Cluster          interface{} `json:"cluster"`
		VirtualChassis   interface{} `json:"virtual_chassis"`
		VcPosition       interface{} `json:"vc_position"`
		VcPriority       interface{} `json:"vc_priority"`
		Comments         string      `json:"comments"`
		LocalContextData interface{} `json:"local_context_data"`
		Tags             []struct {
			ID    int    `json:"id"`
			URL   string `json:"url"`
			Name  string `json:"name"`
			Slug  string `json:"slug"`
			Color string `json:"color"`
		} `json:"tags"`
		CustomFields struct {
			D42ID        interface{} `json:"d42_id"`
			Jira         string      `json:"jira"`
			StatusReason string      `json:"status-reason"`
		} `json:"custom_fields"`
		ConfigContext struct {
		} `json:"config_context"`
		Created     string    `json:"created"`
		LastUpdated time.Time `json:"last_updated"`
	} `json:"results"`
}

type Interface struct {
	Count    int         `json:"count"`
	Next     interface{} `json:"next"`
	Previous interface{} `json:"previous"`
	Results  []struct {
		ID     int    `json:"id"`
		URL    string `json:"url"`
		Device struct {
			ID          int    `json:"id"`
			URL         string `json:"url"`
			Name        string `json:"name"`
			DisplayName string `json:"display_name"`
		} `json:"device"`
		Name  string `json:"name"`
		Label string `json:"label"`
		Type  struct {
			Value string `json:"value"`
			Label string `json:"label"`
		} `json:"type"`
		Enabled      bool          `json:"enabled"`
		Lag          interface{}   `json:"lag"`
		Mtu          interface{}   `json:"mtu"`
		MacAddress   string        `json:"mac_address"`
		MgmtOnly     bool          `json:"mgmt_only"`
		Description  string        `json:"description"`
		Mode         interface{}   `json:"mode"`
		UntaggedVlan interface{}   `json:"untagged_vlan"`
		TaggedVlans  []interface{} `json:"tagged_vlans"`
		Cable        struct {
			ID    int    `json:"id"`
			URL   string `json:"url"`
			Label string `json:"label"`
		} `json:"cable"`
		CablePeer struct {
			ID      int    `json:"id"`
			URL     string `json:"url"`
			Circuit struct {
				ID  int    `json:"id"`
				URL string `json:"url"`
				Cid string `json:"cid"`
			} `json:"circuit"`
			TermSide string `json:"term_side"`
			Cable    int    `json:"cable"`
		} `json:"cable_peer"`
		CablePeerType     string `json:"cable_peer_type"`
		ConnectedEndpoint struct {
			ID      int    `json:"id"`
			URL     string `json:"url"`
			Circuit struct {
				ID  int    `json:"id"`
				URL string `json:"url"`
				Cid string `json:"cid"`
			} `json:"circuit"`
			TermSide string `json:"term_side"`
			Cable    int    `json:"cable"`
		} `json:"connected_endpoint"`
		ConnectedEndpointType      string `json:"connected_endpoint_type"`
		ConnectedEndpointReachable bool   `json:"connected_endpoint_reachable"`
		Tags                       []tagArray
		CountIpaddresses           int `json:"count_ipaddresses"`
	} `json:"results"`
}

type Prefixes struct {
	Count    int         `json:"count"`
	Next     string      `json:"next"`
	Previous interface{} `json:"previous"`
	Results  []struct {
		ID     int    `json:"id"`
		URL    string `json:"url"`
		Family struct {
			Value int    `json:"value"`
			Label string `json:"label"`
		} `json:"family"`
		Prefix string      `json:"prefix"`
		Site   interface{} `json:"site"`
		Vrf    interface{} `json:"vrf"`
		Tenant interface{} `json:"tenant"`
		Vlan   interface{} `json:"vlan"`
		Status struct {
			Value string `json:"value"`
			Label string `json:"label"`
		} `json:"status"`
		Role        RoleStruct `json:"role"`
		IsPool      bool       `json:"is_pool"`
		Description string     `json:"description"`
		Tags        []struct {
			ID    int    `json:"id"`
			URL   string `json:"url"`
			Name  string `json:"name"`
			Slug  string `json:"slug"`
			Color string `json:"color"`
		} `json:"tags"`
		CustomFields struct {
			PrefixPeerIP           string `json:"prefix-peer-ip"`
			PrefixPeeringInterface string `json:"prefix-peering-interface"`
		} `json:"custom_fields"`
		Created     string    `json:"created"`
		LastUpdated time.Time `json:"last_updated"`
	} `json:"results"`
}

type RoleStruct struct {
	Name string `json:"name"`
}

type IPAddresses struct {
	Count    int         `json:"count"`
	Next     interface{} `json:"next"`
	Previous interface{} `json:"previous"`
	Results  []struct {
		ID     int    `json:"id"`
		URL    string `json:"url"`
		Family struct {
			Value int    `json:"value"`
			Label string `json:"label"`
		} `json:"family"`
		Address string      `json:"address"`
		Vrf     interface{} `json:"vrf"`
		Tenant  interface{} `json:"tenant"`
		Status  struct {
			Value string `json:"value"`
			Label string `json:"label"`
		} `json:"status"`
		Role               interface{} `json:"role"`
		AssignedObjectType string      `json:"assigned_object_type"`
		AssignedObjectID   int         `json:"assigned_object_id"`
		AssignedObject     struct {
			ID     int    `json:"id"`
			URL    string `json:"url"`
			Device struct {
				ID          int    `json:"id"`
				URL         string `json:"url"`
				Name        string `json:"name"`
				DisplayName string `json:"display_name"`
			} `json:"device"`
			Name  string `json:"name"`
			Cable int    `json:"cable"`
		} `json:"assigned_object"`
		NatInside   interface{} `json:"nat_inside"`
		NatOutside  interface{} `json:"nat_outside"`
		DNSName     string      `json:"dns_name"`
		Description string      `json:"description"`
		Tags        []struct {
			ID    int    `json:"id"`
			URL   string `json:"url"`
			Name  string `json:"name"`
			Slug  string `json:"slug"`
			Color string `json:"color"`
		} `json:"tags"`
		CustomFields struct {
			BgpPeerIps         string      `json:"bgp-peer-ips"`
			BgpPeerAsn         string      `json:"bgp-peer-asn"`
			BgpPeerName        string      `json:"bgp-peer-name"`
			BgpPrefixLimit     interface{} `json:"bgp-prefix-limit"`
			BgpPeerAsPrepend   int         `json:"bgp-peer-as-prepend"`
			BgpPeerCommunities string      `json:"bgp-peer-communities"`
			BgpPeerMd5         string      `json:"bgp-peer-md5"`
		} `json:"custom_fields"`
		Created     string    `json:"created"`
		LastUpdated time.Time `json:"last_updated"`
	} `json:"results"`
}

type tagArray struct {
	ID    int    `json:"id"`
	URL   string `json:"url"`
	Name  string `json:"name"`
	Slug  string `json:"slug"`
	Color string `json:"color"`
}
