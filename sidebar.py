from __future__ import print_function

from com.moneydance.apps.md.view.gui.sidebar import FullSideBarItemList
from com.moneydance.apps.md.view.gui.sidebar.nodes import SideBarNodeFactory, SideBarNodeType

global moneydance


def export_node(node):
    if node.getChildType() != SideBarNodeType.ACCOUNT:
        return
    acctId = node.getAccountId()
    acct = book.getAccountByNum(acctId)
    active = not acct.getAccountisInactive()
    print(node, acctId, acct, active)

def export_nodes():
    book = moneydance.getCurrentAccountBook()
    mdGUI = moneydance.getUI()
    dtm = SideBarNodeFactory.getBarModelFromSettings(book, mdGUI)
    nodes = SideBarNodeFactory.getNodesFromTree(dtm)
    consume(map(export_node, nodes))

def save_nodes(nodes):
    SideBarNodeFactory.saveNodesToSettings(book, mdGUI, nodes)
