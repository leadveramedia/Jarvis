"""
Asana client for creating and managing tasks.
"""

import os
import asana
from asana.rest import ApiException


class AsanaClient:
    def __init__(self, access_token=None, project_gid=None):
        """Initialize Asana client."""
        self.access_token = access_token or os.environ.get('ASANA_ACCESS_TOKEN')
        self.project_gid = project_gid or os.environ.get('ASANA_PROJECT_GID')

        if not self.access_token:
            raise ValueError("ASANA_ACCESS_TOKEN not found in environment")
        if not self.project_gid:
            raise ValueError("ASANA_PROJECT_GID not found in environment")

        # Configure Asana client (v5 API)
        configuration = asana.Configuration()
        # Strip whitespace/newlines that can cause header errors
        configuration.access_token = self.access_token.strip()
        self.api_client = asana.ApiClient(configuration)
        self.tasks_api = asana.TasksApi(self.api_client)

    def create_task(self, name, notes, assignee_gid=None, follower_gids=None):
        """
        Create a new task in Asana.

        Args:
            name: Task title
            notes: Task description/notes
            assignee_gid: Asana user GID to assign the task to
            follower_gids: List of Asana user GIDs to add as followers

        Returns:
            dict with task info including 'gid' and 'permalink_url'
        """
        task_data = {
            'name': name,
            'notes': notes,
            'projects': [self.project_gid],
        }

        if assignee_gid:
            task_data['assignee'] = assignee_gid

        if follower_gids:
            task_data['followers'] = follower_gids

        try:
            body = {"data": task_data}
            opts = {"opt_fields": "gid,name,permalink_url"}
            result = self.tasks_api.create_task(body, opts)
            # Handle both dict and object responses
            if isinstance(result, dict):
                gid = result.get('gid', '')
                name = result.get('name', '')
                permalink = result.get('permalink_url', '')
            else:
                gid = getattr(result, 'gid', '')
                name = getattr(result, 'name', '')
                permalink = getattr(result, 'permalink_url', '')
            return {
                'success': True,
                'gid': gid,
                'permalink_url': permalink,
                'name': name
            }
        except ApiException as e:
            print(f"Error creating Asana task: {e}")
            return {
                'success': False,
                'error': str(e)
            }
        except Exception as e:
            print(f"Error creating Asana task: {e}")
            return {
                'success': False,
                'error': str(e)
            }
