# AI Agents Platform - User Manual

## Introduction
Welcome to the AI Agents Platform. This platform empowers you to automate complex business processes using a network of specialized AI agents. Whether you are in HR, Finance, Sales, Marketing, IT, or Legal, there is an agent ready to assist you.

## Getting Started

### 1. Accessing the Platform
Open your web browser and navigate to the platform URL (e.g., `http://localhost:8000`). You will be greeted by the login screen.

### 2. Registration & Login
- **Register**: Click "Register", enter a unique username and a strong password.
- **Login**: Enter your credentials to access the dashboard.

## Dashboard Overview
The dashboard provides a centralized view of your activities:
- **Available Agents**: Browse the library of 60+ specialized agents.
- **Active Workflows**: Monitor the status of your running tasks.
- **Analytics**: View real-time performance metrics and event logs.

## Creating a Workflow

1. **Select "New Workflow"**: Click the button in the top navigation bar.
2. **Name Your Workflow**: Give it a descriptive name (e.g., "Monthly Payroll Process").
3. **Add Tasks**:
    - Select an agent from the dropdown (e.g., `hr_payroll_agent_001`).
    - Enter the task details in JSON format. For example:
      ```json
      {
        "period": "November 2025",
        "department": "Engineering"
      }
      ```
4. **Submit**: Click "Create Workflow". The system will dispatch the tasks to the selected agents.

## Monitoring Progress
- Go to the **Workflows** tab.
- Click on a workflow ID to see detailed status.
- You will see real-time updates as agents complete their tasks.

## Viewing Analytics
- Navigate to the **Analytics** section.
- You can see a log of all events, including task start/end times, durations, and success/failure rates.
- This data is streamed in real-time for immediate visibility.

## Support
If you encounter any issues, please contact the IT Support Agent (`it_support_agent_001`) or email support@example.com.
