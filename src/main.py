#!/usr/bin/env python3
"""
Email-to-Asana Automation

Main orchestrator that:
1. Fetches unread emails from Gmail
2. Uses Gemini AI to evaluate if they're actionable
3. Creates Asana tasks for actionable emails
4. Marks processed emails as read
"""

import re
import sys
from gmail_client import GmailClient
from gemini_evaluator import GeminiEvaluator, TEAM_MEMBERS
from asana_client import AsanaClient

# Priority domains - always create tasks for all team members
PRIORITY_DOMAINS = ['businessanywhere.io']


def is_priority_sender(sender):
    """Check if email is from a priority domain."""
    sender_lower = sender.lower()
    return any(domain in sender_lower for domain in PRIORITY_DOMAINS)


def has_unsubscribe_link(body):
    """Check if email body contains unsubscribe-type links (marketing emails)."""
    if not body:
        return False
    body_lower = body.lower()
    unsubscribe_patterns = [
        'unsubscribe',
        'opt-out',
        'opt out',
        'remove me',
        'manage preferences',
        'email preferences',
        'subscription preferences',
        'click here to stop',
        'no longer wish to receive',
    ]
    return any(pattern in body_lower for pattern in unsubscribe_patterns)


def main():
    print("=" * 60)
    print("Email-to-Asana Automation")
    print("=" * 60)

    # Initialize clients
    try:
        print("\nInitializing clients...")
        gmail = GmailClient()
        gemini = GeminiEvaluator()
        asana = AsanaClient()
        print("All clients initialized successfully.")
    except Exception as e:
        print(f"ERROR: Failed to initialize clients: {e}")
        sys.exit(1)

    # Fetch unread emails
    print("\nFetching unread emails...")
    emails = gmail.get_unread_emails(max_results=10)

    if not emails:
        print("No unread emails found.")
        print("\nDone!")
        return

    print(f"Found {len(emails)} unread email(s).")

    # Process each email
    tasks_created = 0
    emails_skipped = 0

    for i, email in enumerate(emails, 1):
        print(f"\n--- Email {i}/{len(emails)} ---")
        print(f"From: {email['sender']}")
        print(f"Subject: {email['subject'][:60]}{'...' if len(email['subject']) > 60 else ''}")

        # Check for unsubscribe links (marketing emails)
        email_content = email['body'] or email['snippet']
        if has_unsubscribe_link(email_content):
            print("  -> Marketing email (has unsubscribe link), skipping.")
            emails_skipped += 1
            gmail.mark_as_read(email['id'])
            print("  -> Marked as read.")
            continue

        # Check for priority senders - create one task with all team members as followers
        if is_priority_sender(email['sender']):
            print("  -> PRIORITY SENDER: Creating task for all team members")
            task_notes = f"""From: {email['sender']}
Date: {email.get('date', 'Unknown')}

Priority email from businessanywhere.io - please review and take action as needed.

---
Original subject: {email['subject']}"""

            all_member_gids = list(TEAM_MEMBERS.values())
            result = asana.create_task(
                name=f"[Priority] {email['subject'][:50]}",
                notes=task_notes,
                follower_gids=all_member_gids
            )
            if result['success']:
                print(f"  -> Task created with all team members as followers")
                tasks_created += 1
            else:
                print(f"  -> ERROR creating task: {result.get('error')}")
        else:
            # Evaluate with Gemini
            print("Evaluating with Gemini...")
            evaluation = gemini.evaluate_email(
                subject=email['subject'],
                body=email_content,
                sender=email['sender']
            )

            if evaluation.get('is_actionable'):
                print(f"  -> ACTIONABLE: Creating task for {evaluation['assignee']}")

                # Create Asana task with sender and date
                task_notes = f"""From: {email['sender']}
Date: {email.get('date', 'Unknown')}

{evaluation['task_notes']}

---
Original subject: {email['subject']}"""

                result = asana.create_task(
                    name=evaluation['task_name'],
                    notes=task_notes,
                    assignee_gid=evaluation['assignee_gid']
                )

                if result['success']:
                    print(f"  -> Task created: {result['name']}")
                    print(f"  -> Assigned to: {evaluation['assignee']}")
                    if result.get('permalink_url'):
                        print(f"  -> URL: {result['permalink_url']}")
                    tasks_created += 1
                else:
                    print(f"  -> ERROR creating task: {result.get('error')}")
            else:
                print("  -> Not actionable, skipping.")
                emails_skipped += 1

        # Mark email as read
        if gmail.mark_as_read(email['id']):
            print("  -> Marked as read.")
        else:
            print("  -> Warning: Failed to mark as read.")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Emails processed: {len(emails)}")
    print(f"Tasks created: {tasks_created}")
    print(f"Emails skipped: {emails_skipped}")
    print("\nDone!")


if __name__ == '__main__':
    main()
