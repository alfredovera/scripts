package main

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"gitlab.ftlio.net/engineering/veritas/neteng/tools/announcer/internal/announcer"
)

var (
	region    string
	asn       string
	server    string
	pathTypes []string
	version   bool
	dryrun    bool
	printTag  bool
	undrained bool
	rootCmd   = &cobra.Command{
		Use:   "",
		Short: "syncs data from netbox/communities YMLs",
		Long:  "syncs data from netbox/communities YMLs",

		Run: func(cmd *cobra.Command, args []string) {
			announcer.CheckArgs(region, asn, server, version, pathTypes, printTag, dryrun, undrained)
		},
	}
)

func init() {
	rootCmd.PersistentFlags().BoolVarP(&dryrun, "dryrun", "d", false, "will run the script but will not push to billboard cloud")
	rootCmd.PersistentFlags().BoolVarP(&printTag, "print", "", false, "shows the billboard generated output")
	rootCmd.PersistentFlags().BoolVarP(&undrained, "undrained", "", false, "will default new advertisements to an undrained state")
	rootCmd.PersistentFlags().BoolVarP(&version, "version", "v", false, "gives the announcer version")
	rootCmd.PersistentFlags().StringVarP(&region, "region", "r", "", "input the region of the asn you want to generate advertisements")
	rootCmd.PersistentFlags().StringVarP(&asn, "asn", "a", "", "input the asn for the server or region")
	rootCmd.PersistentFlags().StringVarP(&server, "server", "s", "", "input the server hostname")
	rootCmd.PersistentFlags().StringArrayVarP(&pathTypes, "path_types", "p", []string{}, "input the path types to generate advertisements")
	rootCmd.MarkFlagRequired("path_types")
}

func main() {
	err := rootCmd.Execute()
	if err != nil {
		fmt.Fprintf(os.Stderr, "%v\n", err)
		os.Exit(1)
	}
	os.Exit(0)
}
