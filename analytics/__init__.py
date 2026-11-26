"""Railway analytics package for KPIs, train search, and route analysis."""

from analytics.kpis import compute_dashboard_kpis
from analytics.route_analysis import (
    get_busiest_stations,
    get_longest_and_shortest_routes,
    get_train_route_profile,
)
from analytics.search import search_between_stations, search_by_station, search_by_train_number

__all__ = [
    "compute_dashboard_kpis",
    "get_busiest_stations",
    "get_longest_and_shortest_routes",
    "get_train_route_profile",
    "search_between_stations",
    "search_by_station",
    "search_by_train_number",
]
