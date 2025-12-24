import requests
import getpass
import sys

REPO = "rikksullenber/mealie-ai"
HUB_API_BASE = "https://hub.docker.com/v2"
REGISTRY_API_BASE = "https://index.docker.io/v2"

def login_hub():
    """Logs into Docker Hub API to get a JWT token."""
    print("Logging into Docker Hub...")
    username = input("Docker Hub Username: ")
    password = getpass.getpass("Docker Hub Password (or Access Token): ")
    
    resp = requests.post(f"{HUB_API_BASE}/users/login", json={"username": username, "password": password})
    if resp.status_code != 200:
        print(f"Failed to login to Hub: {resp.text}")
        sys.exit(1)
    
    return resp.json()["token"], username, password

def get_registry_token(username, password):
    """Gets a token for the Docker Registry API allowing deletion."""
    print("Getting Registry Token...")
    # Scope for pull, push, and delete (*)
    scope = f"repository:{REPO}:pull,push,*"
    url = f"https://auth.docker.io/token?service=registry.docker.io&scope={scope}"
    
    resp = requests.get(url, auth=(username, password))
    if resp.status_code != 200:
        print(f"Failed to get registry token: {resp.text}")
        sys.exit(1)
        
    return resp.json()["token"]

def get_tags_and_digests(hub_token):
    """Fetches all tags and their digests from Docker Hub."""
    headers = {"Authorization": f"JWT {hub_token}"}
    tags_by_digest = {} # digest -> list of tags
    all_tags = []
    
    url = f"{HUB_API_BASE}/repositories/{REPO}/tags?page_size=100"
    
    print("Fetching tags and digests...", end="", flush=True)
    while url:
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            print(f"\nError fetching tags: {resp.text}")
            break
        
        data = resp.json()
        for result in data.get("results", []):
            tag_name = result["name"]
            # Prefer 'digest' field, fallback to checking images list
            digest = result.get("digest") 
            if not digest and result.get("images"):
                # Use the digest of the first architecture (often amd64 or simple match)
                # Ideally we track multi-arch manifests, but top-level digest is sufficient for deletion
                digest = result["images"][0].get("digest")

            if digest:
                if digest not in tags_by_digest:
                    tags_by_digest[digest] = []
                tags_by_digest[digest].append(tag_name)
            
            all_tags.append({"name": tag_name, "digest": digest})
        
        url = data.get("next")
        print(".", end="", flush=True)
    print("\n")
    return all_tags, tags_by_digest

def delete_manifest(registry_token, digest):
    """Deletes a manifest by digest using the Registry API."""
    headers = {
        "Authorization": f"Bearer {registry_token}",
        "Accept": "application/vnd.docker.distribution.manifest.v2+json"
    }
    url = f"{REGISTRY_API_BASE}/{REPO}/manifests/{digest}"
    resp = requests.delete(url, headers=headers)
    return resp.status_code in [202, 200, 404] # 202 accepted, 200 ok, 404 already gone

def delete_tag_only(hub_token, tag):
    """Deletes a tag using the Hub API."""
    headers = {"Authorization": f"JWT {hub_token}"}
    url = f"{HUB_API_BASE}/repositories/{REPO}/tags/{tag}"
    resp = requests.delete(url, headers=headers)
    return resp.status_code == 204

def main():
    print(f"Preparing to purge 'alpha' tags and manifests from {REPO}")
    
    # 1. Login
    hub_token, username, password = login_hub()
    registry_token = get_registry_token(username, password)
    
    # 2. Analyze Tags
    all_tags, tags_by_digest = get_tags_and_digests(hub_token)
    
    alpha_tags = [t for t in all_tags if "alpha" in t["name"]]
    
    if not alpha_tags:
        print("No tags containing 'alpha' found.")
        return

    print(f"Found {len(alpha_tags)} tags containing 'alpha'.")
    
    # 3. Plan Deletion
    to_delete_manifests = set()
    to_delete_tags_only = []
    
    print("\nAnalysis:")
    for tag_obj in alpha_tags:
        tag = tag_obj["name"]
        digest = tag_obj["digest"]
        
        if not digest:
            print(f" - {tag}: No digest found. Will delete tag only.")
            to_delete_tags_only.append(tag)
            continue
            
        # Check who else shares this digest
        sharing_tags = tags_by_digest.get(digest, [])
        # Filter out other alpha tags to see if any "safe" tags remain
        safe_tags = [t for t in sharing_tags if "alpha" not in t]
        
        if len(safe_tags) == 0:
            print(f" - {tag}: Exclusive to alpha versions. Will delete MANIFEST {digest[:12]}...")
            to_delete_manifests.add(digest)
            to_delete_tags_only.append(tag)
        else:
            print(f" - {tag}: Digest shared with {safe_tags}. Will delete TAG ONLY.")
            to_delete_tags_only.append(tag)

    total_ops = len(to_delete_manifests) + len(to_delete_tags_only)
    if total_ops == 0:
        print("Nothing to do.")
        return

    # 4. Confirm
    print(f"\nPLAN: Delete {len(to_delete_manifests)} Manifests (Data) and {len(to_delete_tags_only)} Tags (Pointers).")
    confirm = input("Type 'yes' to execute this DESTRUCTIVE operation: ")
    if confirm.lower() != "yes":
        print("Cancelled.")
        return

    # 5. Execute
    print("\nExecuting...")
    
    # Delete manifests first (cleans up associated tags automatically usually, but we can be explicit)
    for digest in to_delete_manifests:
        print(f"Deleting Manifest {digest[:12]}...", end=" ")
        if delete_manifest(registry_token, digest):
            print("OK")
        else:
            print("FAILED")
            
    # Delete remaining tags
    for tag in to_delete_tags_only:
        print(f"Deleting Tag {tag}...", end=" ")
        if delete_tag_only(hub_token, tag):
            print("OK")
        else:
            print("FAILED")

    print("\nDone.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
