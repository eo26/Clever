# Product Guidelines - Clever Data Project

## Introduction
These guidelines define the core principles for communication, user experience, and visual design to ensure a consistent and positive experience for students and parents.

## Prose Style
- **Tone:** **Friendly & Encouraging.** Use accessible language that empowers students and parents to understand their academic data without technical jargon.
- **Voice:** Active and helpful. For example, instead of "Error: Token Expired," use "It looks like your access token has expired. Please refresh it to see your latest grades!"

## Visual & Information Design
- **Aesthetic:** **Structured & Informative.** Focus on clearly delineated sections with informative headers to make data easy to scan.
- **Data Display:** Use standard CLI tables or well-structured lists for grades and assignments, ensuring that high-priority information (like due dates and current scores) is prominent.

## User Experience (UX) Principles
- **Efficiency First:** Prioritize fast data retrieval and minimize the steps required for a user to get their daily or weekly academic summary.
- **Data Integrity:** Ensure that all data presented is accurate and consistent with the source (Canvas LMS). If data is unavailable or restricted, clearly indicate this rather than omitting it without explanation.

## Error & Status Handling
- **Graceful & Simplified:** When issues occur (e.g., network timeouts or API errors), provide high-level summaries and graceful fallbacks rather than overwhelming the user with technical stack traces.
- **Actionable Status:** Inform the user when the tool is actively fetching data and provide a clear "next step" if an operation cannot be completed.
