#!/usr/bin/env python3
"""Provides airport information lookup by IATA code"""
import argparse
import json
import os

import requests

AIRPORT_DATA_URL = "https://datahub.io/core/airport-codes/r/airport-codes.json"
AIRPORT_DATA_FILE = ".data_airports.json"


class Airport:
    def __init__(self, data):
        # encoding/decoding because the source data file is broken.
        # and encodes the unicode codepoints as separate escape sequeces
        self.iata = data["iata_code"]
        self.name = data["name"].encode("latin1").decode("utf-8")
        self.continent = data["continent"]
        self.iso_country = data["iso_country"]
        self.coordinates = data["coordinates"]
        self.municipality = data["municipality"]
        if data["municipality"] is not None:
            self.municipality = self.municipality.encode("latin1").decode("utf-8")

    def __str__(self):
        return (
            f"{self.name}\n"
            f"  Coordiantes:  {self.coordinates}\n"
            f"  Contient:     {self.continent}\n"
            f"  ISO Country:  {self.iso_country}\n"
            f"  Municipality: {self.municipality}\n"
        )


class Airports(object):
    def __init__(self):
        self.airports = {}
        self.cache_file = os.path.join(os.path.dirname(__file__), AIRPORT_DATA_FILE)

        # download data file, if it doesn't already exist
        if not os.path.isfile(self.cache_file):
            print(f"Downloading airport data from {AIRPORT_DATA_URL}...")
            download_store_content(url=AIRPORT_DATA_URL, filelocation=self.cache_file)

        # build hash table
        with open(self.cache_file, encoding="utf-8") as airportfile:
            for ap in json.load(airportfile):
                iata = ap["iata_code"]
                if iata is not None:
                    self.airports[iata] = Airport(ap)

    def lookup(self, iata):
        return self.airports.get(iata.upper())


def download_store_content(url: str, filelocation: str) -> None:
    try:
        r = requests.get(url)
        r.raise_for_status()
    except Exception:
        print("Could not retrieve the file for regional data.")
        raise

    with open(filelocation, "wb") as f:
        f.write(r.content)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lookup airport information")
    parser.add_argument("iata", type=str, help="The IATA airport code to lookup")
    args = parser.parse_args()

    airports = Airports()
    print(airports.lookup(args.iata))
