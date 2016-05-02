#!/usr/bin/env python2.7

import os
import webbrowser
from pprint import pprint


#SMF Employee List
AVERA = {'username': 'avera', 'fullname': 'Alfredo Vera', 'title': 'Sr Site Ops Tech'}
MERTZ = {'username': 'mertz', 'fullname': 'Michael Ertz', 'title': 'Sr Site Ops Tech'}
ADAMCASTRO = {'username': 'adamcastro', 'fullname': 'Adam Castro', 'title': 'Site Ops Tech II'}
SUN = {'username': 'sun', 'fullname': 'Scott Un', 'title': 'Site Ops Tech II'}

#ATL Employee List
JNASH = {'username': 'jnash', 'fullname': 'Joseph Nash', 'title': 'Site Ops Tech I'}
DRUGGE = {'username': 'drugge', 'fullname': 'David Rugge', 'title': 'Site Ops Tech II'}
INATHANSON = {'username': 'inathanson', 'fullname': 'Ian Nathanson', 'title': 'Sr Site Ops Tech'}
JGILBREATH = {'username': 'jgilbreath', 'fullname': 'Jeff Gilbreath', 'title': 'Site Ops Tech II'}

SMF_TEAMS_DICT = {'Intake': [AVERA, MERTZ],
                  'Repairs': [ADAMCASTRO, SUN]}
ATL_TEAMS_DICT = {'Intake': [INATHANSON, JGILBREATH],
                  'Repairs': [JNASH, DRUGGE]}

SITES = {'SMF': SMF_TEAMS_DICT,
         'ATL': ATL_TEAMS_DICT,
         'RIC': None}


def present_menu(menu_items_dict, prompt):
    """
    Presents menu to user:
    Arguments:
        menu_items_dict = dictionary
            Menu items to display.
        prompt = string
            Prompt for display.
    """
    menu = sorted(menu_items_dict)
    print_menu(menu)
    choice = raw_input("Choose %s: " % prompt)
    chosen = determine_choice(menu, menu_items_dict, choice)
    take_action(chosen, prompt)


def print_menu(menu):
    """
    Prints Menu:
    Arguments:
        menu = list of strings.
            Choices to print out to user.
    """
    for num, element in enumerate(menu, 1):
        print("%d. %s" % (num, element))


def determine_choice(menu, a_dict, choice):
    """
    Prints user choice:
    Arguments:
        menu = list of strings.
            Choices to print out to user.
        a_dict = dictionary
            Menu items to display.
        choice = string.
            users choice.
    Returns: dictionary
    """
    if choice.isdigit():
        name = menu[int(choice) - 1]
    elif choice in a_dict:
        name = choice
    else:
        print("\nInvalid Choice, Try Again")
        datacenter()

    print("%s" % name)
    return a_dict[name]


def take_action(action, prompt):
    """
    Takes action:
    Arguments:
        action = dictionary or list
            Takes user choice
        prompt = string
            user data.
    """
    if isinstance(action, dict):
      present_menu(action, prompt)
    elif isinstance(action, list):
      menu = {}
      for person in action:
        fullname = person['fullname']
        username = person['username']
        menu[fullname] = open_browser, username
      present_menu(menu, 'Employee')
    elif isinstance(action, tuple):
      func, arg = action
      func(arg)


def open_browser(username):
    """
    Opens webbrowser based on username chosen.
    Arguments:
        username = str ldap name
    """
    webbrowser.open('https://birdhouse.twitter.biz/people/profile/' + username)


def main():
    """Main function."""
    present_menu(SITES, 'Datacenter')


if __name__ == '__main__':
    main()
