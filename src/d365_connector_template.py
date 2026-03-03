"""
Template: Connect to Microsoft Dataverse / Dynamics 365 Web API.

This module is a **reference stub** — it contains no credentials and does not
make live calls.  Use it as a starting point when integrating with a real
Dynamics 365 / Dataverse environment.

Typical setup steps
-------------------
1. **Register an app in Azure Entra ID**
   - Azure portal → App registrations → New registration
   - Add API permission: Dynamics CRM → user_impersonation (or application-level)
   - Create a client secret (or use a certificate for production)

2. **Acquire an access token with MSAL**
   - Install: ``pip install msal``
   - Use ``ConfidentialClientApplication`` for service-to-service (daemon) flows::

       app = msal.ConfidentialClientApplication(
           client_id, authority=f"https://login.microsoftonline.com/{tenant_id}",
           client_credential=client_secret,
       )
       result = app.acquire_token_for_client(
           scopes=[f"{base_url}/.default"]
       )
       access_token = result["access_token"]

3. **Call Dataverse Web API**
   - Base URL pattern: ``https://<org>.crm.dynamics.com``
   - All endpoints live under ``/api/data/v9.2/``
   - Use OData query options ($select, $filter, $top, $expand) for efficient reads
"""
from __future__ import annotations

import requests


def dataverse_get_whoami(access_token: str, base_url: str) -> dict:
    """
    Call the WhoAmI endpoint and return the response payload as a dict.

    Parameters
    ----------
    access_token : str
        Bearer token obtained from MSAL / Azure Entra ID.
    base_url : str
        Root URL of the Dataverse org, e.g. ``https://myorg.crm.dynamics.com``.

    Returns
    -------
    dict
        JSON response containing UserId, BusinessUnitId, OrganizationId.
    """
    url = f"{base_url.rstrip('/')}/api/data/v9.2/WhoAmI"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
    }
    r = requests.get(url, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()


def dataverse_query_table(
    access_token: str,
    base_url: str,
    logical_name: str,
    select: list[str] | None = None,
    top: int = 100,
) -> list[dict]:
    """
    Query a Dataverse table and return a list of record dicts.

    Parameters
    ----------
    access_token : str
        Bearer token obtained from MSAL / Azure Entra ID.
    base_url : str
        Root URL of the Dataverse org, e.g. ``https://myorg.crm.dynamics.com``.
    logical_name : str
        Plural logical name of the entity, e.g. ``"incidents"`` for Cases or
        ``"opportunities"`` for Opportunities.
    select : list[str] | None
        Column names to include in ``$select``.  If None, all columns are returned.
    top : int
        Maximum number of records to retrieve (``$top``).  Defaults to 100.

    Returns
    -------
    list[dict]
        List of record dicts from the ``value`` key of the OData response.

    Example
    -------
    ::

        records = dataverse_query_table(
            token, "https://myorg.crm.dynamics.com",
            logical_name="incidents",
            select=["title", "prioritycode", "createdon"],
            top=500,
        )
    """
    url = f"{base_url.rstrip('/')}/api/data/v9.2/{logical_name}"
    params: dict[str, str] = {"$top": str(top)}
    if select:
        params["$select"] = ",".join(select)

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "OData-MaxVersion": "4.0",
        "OData-Version": "4.0",
    }
    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("value", [])
