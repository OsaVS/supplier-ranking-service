"""
Connectors package for the Supplier Ranking System.
This package provides integration with other components of the supply chain management system.
"""

from .group29_connector import Group29Connector
from .group30_connector import Group30Connector
from .group32_connector import Group32Connector

__all__ = [
    'Group29Connector',
    'Group30Connector',
    'Group32_connector'
]