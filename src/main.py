#!/usr/bin/env python3
"""
Email-to-Asana Automation

Main orchestrator that:
1. Fetches unread emails from Gmail
2. Uses Gemini AI to evaluate if they're actionable
3. Creates Asana tasks for actionable emails
4. Marks processed emails as read
"""

import sys
from gmail_client import GmailClient
from gemini_evaluator import GeminiEvaluator
from asana_client import AsanaClient


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
    emails = gmail.get_unread_emails(max_results=20)

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

        # Evaluate with Gemini
        print("Evaluating with Gemini...")
        evaluation = gemini.evaluate_email(
            subject=email['subject'],
            body=email['body'] or email['snippet'],
            sender=email['sender']
        )

        if evaluation.get('is_actionable'):
            print(f"  -> ACTIONABLE: Creating task for {evaluation['assignee']}")

            # Create Asana task
            result = asana.create_task(
                name=evaluation['task_name'],
                notes=f"From: {email['sender']}\n\n{evaluation['task_notes']}\n\n---\nOriginal subject: {email['subject']}",
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
