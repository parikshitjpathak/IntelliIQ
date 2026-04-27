import os
import requests
from requests.auth import HTTPBasicAuth


# ==========================================================
# FUNCTION: create_jira_ticket
# ==========================================================

def create_jira_ticket(summary, description, due_date):
    url = os.getenv("JIRA_URL") + "/rest/api/3/issue"

    auth = HTTPBasicAuth(
        os.getenv("JIRA_EMAIL"),
        os.getenv("JIRA_API_TOKEN")
    )

    payload = {
        "fields": {
            "project": {"key": os.getenv("JIRA_PROJECT_KEY")},
            "summary": summary,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{
                        "type": "text",
                        "text": description
                    }]
                }]
            },
            "issuetype": {"name": "Task"},
            #"duedate": due_date.strftime("%Y-%m-%d")
            #"duedate": due_date[:10]
            "duedate": due_date
        }
    }

    response = requests.post(url, json=payload, auth=auth)
    result = response.json()

    if "key" not in result:
        raise Exception(f"Jira Error: {result}")

    return result["key"]


# ==========================================================
# FUNCTION: add_jira_comment
# ==========================================================

def add_jira_comment(issue_key, page_link):
    url = os.getenv("JIRA_URL") + f"/rest/api/3/issue/{issue_key}/comment"

    auth = HTTPBasicAuth(
        os.getenv("JIRA_EMAIL"),
        os.getenv("JIRA_API_TOKEN")
    )

    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "Confluence Page: "},
                    {
                        "type": "text",
                        "text": "View Knowledge Base",
                        "marks": [{
                            "type": "link",
                            "attrs": {"href": page_link}
                        }]
                    }
                ]
            }]
        }
    }

    requests.post(url, json=payload, auth=auth)


# ==========================================================
# FUNCTION: create_confluence_page
# ==========================================================

def create_confluence_page(incident, impact, root_cause, resolution, jira_key):

    base_url = os.getenv("CONFLUENCE_URL")
    space_key = os.getenv("CONFLUENCE_SPACE_KEY")

    auth = HTTPBasicAuth(
        os.getenv("CONFLUENCE_EMAIL"),
        os.getenv("CONFLUENCE_API_TOKEN")
    )

    title = f"{jira_key} | {incident}"

    # ✅ VERY IMPORTANT: DO NOT FORMAT HERE
    # We directly use what is passed (plain text)

    #changing this on 17th april to pass jira ticket link to confluence page content = root_cause

    jira_url = f"{os.getenv('JIRA_URL')}/browse/{jira_key}"

    content = f"""{root_cause}

    <p><b>Ticket ID:</b> <a href="{jira_url}" target="_blank">{jira_key}</a></p>
    """


    #17th april changes completed

    # ==========================================================
    # CHECK IF PAGE EXISTS
    # ==========================================================

    search_url = f"{base_url}/rest/api/content?title={title}&spaceKey={space_key}"

    search_response = requests.get(search_url, auth=auth)
    search_data = search_response.json()

    if search_data.get("results"):
        # UPDATE EXISTING PAGE
        page = search_data["results"][0]
        page_id = page["id"]

        detail_url = f"{base_url}/rest/api/content/{page_id}?expand=version"
        detail_response = requests.get(detail_url, auth=auth)
        detail_data = detail_response.json()

        current_version = detail_data["version"]["number"]

        update_url = f"{base_url}/rest/api/content/{page_id}"

        payload = {
            "id": page_id,
            "type": "page",
            "title": title,
            "version": {"number": current_version + 1},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }

        response = requests.put(update_url, json=payload, auth=auth)
        result = response.json()

    else:
        # CREATE NEW PAGE
        create_url = f"{base_url}/rest/api/content"

        payload = {
            "type": "page",
            "title": title,
            "space": {"key": space_key},
            "body": {
                "storage": {
                    "value": content,
                    "representation": "storage"
                }
            }
        }

        response = requests.post(create_url, json=payload, auth=auth)
        result = response.json()

    # ==========================================================
    # RETURN LINK
    # ==========================================================

    if "_links" in result:
        return result["_links"]["base"] + result["_links"]["webui"]
    else:
        print("Confluence Error:", result)
        return None