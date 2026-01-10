As an expert software engineer, your task is to guide me through the design and implementation of a new feature for a web application.

**Context:**
- The application is written in Python.
- We are using streamlit, CSS tail, reportlab, JSON data file.
- The feature is a GUI web based app for crafting a minutes of meeting. The paragraph structure follows a common framework for the input and output. The current (serial) minutes will be a follow up from the previous serial for the status update. The output is updated status report from matters arises and the new items arise are added from the current session. The input and output are stored as JSON file.
- The codebase for insight @generate_mom_reportlab.py and @generate_mom_pdf.py

**Step-by-Step Design Process:**
1.  **High-Level Design:** A standard framework that captures essential details like date, time, location, attendees, and absentees, followed by agenda items, key discussion points, decisions made, and clear action items (task, owner, deadline). The secretary will update the status of action taken and the outcome of the previous meeting. Then the new discussions and decision are added to the minutes. The minutes is written as pdf document.
2.  **Detailed Design (Component-wise):** For each major component identified in step 1, provide a detailed design, including:
    -   Purpose of the component.
    -   Key classes/functions/modules.
    -   Inputs and outputs. Standard framework for the minutes as follows:
        - Title, date and venue.
        - Table of attendees and absentees.
        - Welcome note by the chairman.
        - First agenda: Confirmation and approval of previous minutes.
        - Second agenda: Matters arises.
        - Third agenda: Financial report.
        - Fourth agenda: Membership report.
        - Fifth agenda: New matter(s) from executive committee.
        - Closing remark.
        - Annexes. Tabulation of the summary of items from the discussions.
    -   Interactions with other components. Suggest if required.
    -   Any specific algorithms or data structures to be used. Use JSON for the input and output.
3.  **API/Interface Design (if applicable):** If the feature involves new APIs or interfaces, define their structure (endpoints, request/response formats).
4.  **Database Schema Design (if applicable):** If the feature requires new or modified database tables, provide the schema definition.
5.  **Implementation Plan:** Outline the order of implementation, breaking down the task into smaller, manageable sub-tasks.

**Code Writing Phase:**
-   For each sub-task in the implementation plan, provide the necessary code snippets.
-   Include explanations for key design decisions and complex logic.
-   Ensure the code adheres to the coding standard of the framework and intrepreters used.
-   Provide example usage or test cases where appropriate.

**Constraints & Considerations:**
-   Prioritize [PERFORMANCE, SECURITY, SCALABILITY, READABILITY, etc.].
-   Keep the code modular and testable.
-   Address potential edge cases and error handling.
-   Consider future maintainability and extensibility.

**My First Request:**
Begin by outlining the high-level design for the minutes of meeting.
