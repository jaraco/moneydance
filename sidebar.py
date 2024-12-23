"""
Export and import the accounts from the sidebar.
"""

from __future__ import print_function

import os
import __main__

from com.moneydance.apps.md.view.gui.sidebar import FullSideBarItemList
from com.moneydance.apps.md.view.gui.sidebar.nodes import (
    SideBarNodeFactory,
    SideBarNodeType,
)

moneydance = __main__.moneydance


default_name = os.path.join(os.path.dirname(__file__), "sidebar accounts.txt")


def _is_account(node):
    return node.getChildType() == SideBarNodeType.ACCOUNT


def _load_nodes():
    book = moneydance.getCurrentAccountBook()
    mdGUI = moneydance.getUI()
    dtm = SideBarNodeFactory.getBarModelFromSettings(book, mdGUI)
    return SideBarNodeFactory.getNodesFromTree(dtm)


def export(dest=default_name):
    account_nodes = filter(_is_account, _load_nodes())
    with open(dest, "w") as outf:
        outf.writelines(str(node) + "\n" for node in account_nodes)


def import_(src=default_name, dry_run=True):
    current = _load_nodes()
    with open(src) as inf:
        expected = [line.strip() for line in inf]
    remove_nodes = [
        node for node in current if _is_account(node) and str(node) not in expected
    ]
    if not remove_nodes:
        print("Nothing to remove")
        return
    action = "Simulating removing" if dry_run else "Removing"
    print(action, remove_nodes, "from sidebar")
    if dry_run:
        return
    for node in remove_nodes:
        current.remove(node)
    _save_nodes(current)


def _save_nodes(nodes):
    book = moneydance.getCurrentAccountBook()
    mdGUI = moneydance.getUI()
    SideBarNodeFactory.saveNodesToSettings(book, mdGUI, nodes)
