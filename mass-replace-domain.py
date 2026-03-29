#!/usr/bin/env python3
"""
1password-set-exact-host.py

For all items across all vaults whose URL contains TARGET_DOMAIN,
sets the autofill behavior on matching URLs to ExactMatch
("Only fill on this exact host").
"""

import asyncio
import os

from dotenv import load_dotenv
from onepassword import AutofillBehavior
from onepassword.types import (
    Item,
    ItemCreateParams,
    ItemCategory,
    ItemOverview,
    Vault,
    Website
)
from onepassword.client import Client, DesktopAuth

load_dotenv()
TARGET_DOMAIN = os.getenv('TARGET_DOMAIN')
DOMAIN_TO_REPLACE_TARGET_DOMAIN = os.getenv('DOMAIN_TO_REPLACE_TARGET_DOMAIN')


async def main():
    # --- Auth: uses your local 1Password desktop app (biometrics/password prompt) ---
    # Replace "your-account-name" with your account name as shown in 1Password
    client = await Client.authenticate(
        auth=DesktopAuth(account_name="DiSanti"),
        integration_name="Set Exact Host Autofill",
        integration_version="v1.0.0",
    )

    print(f"Scanning all vaults for URLs containing: {TARGET_DOMAIN}\n")

    vaults = await client.vaults.list()


    for vault in vaults:
        if vault.id == os.getenv('IGNORE_VAULT_ID', "None"): continue # the fake 'Personal' vault, for example
        
        try:
            items = await client.items.list(vault.id)
            print(f"Scanning vault [{vault.title} ({vault.id})]. Total items: {len(items)}")

            for item_overview in items:
                
                try:
                
                    # We only care about items with sites
                    if not item_overview.websites: continue
                    
                    # Check if the item has a site with our filter
                    matching_site = False
                    for site in item_overview.websites:
                        if TARGET_DOMAIN in site.url:
                            matching_site = True
                            break
                    
                    # If the item does not have the website we are interested in, skip it
                    if not matching_site: continue
                    # if item_overview.title != "<item name to debug>": continue
                    
                    # Fetch the full item (expensive); we are confident it has a website we need to modify
                    item = await client.items.get(vault.id, item_overview.id)
                    
                    for site in item.websites:
                        if TARGET_DOMAIN in site.url:
                            site.url = site.url.replace(TARGET_DOMAIN, DOMAIN_TO_REPLACE_TARGET_DOMAIN) # only replaces substrings, not the entire string
                    
                    # Commit changes to 1Password
                    updated_item = await client.items.put(item)
                    print(f"Updated item: {updated_item.title}")
                
                except Exception as e:
                    try: print(f"Error on item: {item_overview.title}: {e}")
                    except Exception: print(f"Super error: {e}")
                    continue
                
    
        except Exception as e:
            if "permissions" in str(e).lower():
                print(f"Skipped vault [{vault.title} ({vault.id})] (probably inactive duplicate)")

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())