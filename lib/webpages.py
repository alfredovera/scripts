import typing
import webbrowser
from urllib.parse import quote_plus


def web_grafana_pop_health(server: str) -> None:
    graf_path = "https://grafana.global.ftlprod.net"
    server_short = server.replace("-data01", "")

    pop_health = f"{graf_path}/d/4JEipO57k/pop-health?var-pop={server_short}&var-level=All&var-services=All&var-server={server}&var-filter=&refresh=30s"  # noqa
    webbrowser.open(pop_health)


def web_grafana_globalturn_pop_overview(server: str) -> None:
    graf_path = "https://grafana.global.ftlprod.net"
    turn_health = f"{graf_path}/d/Yoi5Rlcnk/overview-per-pop?orgId=1&refresh=30s&var-realm=All&var-instance={server}&from=now-5m&to=now&refresh=30s"  # noqa
    webbrowser.open(turn_health)


def web_graph(graph: typing.Any, alpha: bool = False) -> None:
    quoted_popid = quote_plus(graph.pop_id)
    if alpha:
        graph_url = f"https://graph.subspace-alpha.com/pops/{quoted_popid}/details"
    else:
        graph_url = f"https://graph.subspace.com/pops/{quoted_popid}/details"
    webbrowser.open(graph_url)


def web_alice(server: str, as_number: str = None) -> None:
    alice_url = f"https://looking-glass.ftlprod.net/routeservers/{server}"
    if as_number:
        alice_url = f"{alice_url}?s=asn&o=asc&q={as_number}"
    webbrowser.open(alice_url)


def web_api_health() -> None:
    api_health_url = (
        "https://grafana.global.ftlprod.net/d/ApdbczCGz/api-health?orgId=1&refresh=5s"
    )
    webbrowser.open(api_health_url)


def web_netbox_device(nb_server: typing.Any) -> None:
    webbrowser.open(f"https://netbox.global.ftlprod.net/dcim/devices/{nb_server.id}")
