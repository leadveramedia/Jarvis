"""
Gemini AI evaluator for determining if emails are actionable.
"""

import json
import os
import google.generativeai as genai

# Team member mapping with Asana GIDs
TEAM_MEMBERS = {
    "Anna": "1210895765709613",   # Arizona ABS, Google ads, social media for Leadvera
    "Max": "1210895765692974",    # Frank Penney, Compass, Google ads, social ads
    "Roger": "1210895765247998",  # MARV Media ops, Leadvera Media ops, tech/engineering
}
DEFAULT_ASSIGNEE = "Roger"


class GeminiEvaluator:
    def __init__(self, api_key=None):
        """Initialize Gemini evaluator."""
        api_key = api_key or os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        # Strip whitespace/newlines that can cause gRPC header errors
        genai.configure(api_key=api_key.strip())
        self.model = genai.GenerativeModel('gemini-3-flash-preview')

    def evaluate_email(self, subject, body, sender):
        """
        Evaluate an email and determine if it's actionable.

        Returns:
            dict with keys: is_actionable, task_name, task_notes, assignee, assignee_gid
        """
        prompt = f"""You are an executive assistant. Analyze the following email and determine:
1. Is this email actionable? (requires a task to be created)
2. If actionable, create a concise task name
3. If actionable, summarize what needs to be done
4. Assign to the appropriate team member

Emails that are NOT actionable:
- Newsletter updates, marketing emails, spam
- Simple "thank you" or acknowledgment emails
- Automated notifications that don't require action
- FYI/informational emails with no action needed

Emails that ARE actionable:
- Requests for meetings or calls
- Bug reports or technical issues
- Direct questions requiring response
- Tasks or deliverable requests
- Client requests or feedback needing action

TEAM MEMBERS - Assign based on context:
- Anna: Arizona ABS projects, Google Ads management, social media accounts for Leadvera
- Max: Frank Penney projects, Compass projects, Google Ads, social ads campaigns
- Roger: Operations for MARV Media and Leadvera Media, technical issues, engineering tasks (DEFAULT if unclear)

EMAIL TO ANALYZE:
From: {sender}
Subject: {subject}
Body: {body}

Respond ONLY with a valid JSON object (no markdown, no code blocks):
{{"is_actionable": true or false, "task_name": "concise task title or empty string", "task_notes": "brief summary of what needs to be done or empty string", "assignee": "Anna" or "Max" or "Roger"}}
"""

        try:
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text)

            # Add assignee GID
            assignee_name = result.get('assignee', DEFAULT_ASSIGNEE)
            if assignee_name not in TEAM_MEMBERS:
                assignee_name = DEFAULT_ASSIGNEE
            result['assignee'] = assignee_name
            result['assignee_gid'] = TEAM_MEMBERS[assignee_name]

            return result

        except Exception as e:
            print(f"Error evaluating email: {e}")
            return {
                'is_actionable': False,
                'task_name': '',
                'task_notes': '',
                'assignee': DEFAULT_ASSIGNEE,
                'assignee_gid': TEAM_MEMBERS[DEFAULT_ASSIGNEE],
                'error': str(e)
            }

    def _parse_response(self, response_text):
        """Parse Gemini's JSON response."""
        # Clean up response - remove markdown code blocks if present
        cleaned = response_text.strip()
        cleaned = cleaned.replace('```json', '').replace('```', '').strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            print(f"Failed to parse Gemini response: {response_text}")
            print(f"JSON error: {e}")
            # Return safe default
            return {
                'is_actionable': False,
                'task_name': '',
                'task_notes': '',
                'assignee': DEFAULT_ASSIGNEE
            }
