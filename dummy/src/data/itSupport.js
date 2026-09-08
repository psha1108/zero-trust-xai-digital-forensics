export const IT_SUPPORT_DATA = [
  {
    id: "IT-DEV-001",
    title: "Device Maintenance Guidelines",
    category: "IT Support",
    sensitivity: "Internal",
    version: "1.2",
    description: "Guidelines for keeping company-issued devices secure and functioning optimally.",
    sections: [
      { title: "1. Updates", content: "Always install OS and security updates within 48 hours of notification." },
      { title: "2. Physical Security", content: "Do not leave devices unattended in public spaces. Always lock your screen when away." },
      { title: "3. Maintenance", content: "Restart your machine at least once a week to apply background updates." }
    ]
  },
  {
    id: "IT-SVC-001",
    title: "IT Service Desk Information",
    category: "IT Support",
    sensitivity: "Internal",
    version: "2.0",
    description: "How to contact IT Support and SLAs for different priority issues.",
    sections: [
      { title: "1. Contacting Support", content: "Submit a ticket via the IT Portal or call the 24/7 hotline for critical issues." },
      { title: "2. Service Level Agreements (SLAs)", content: "• Critical: 1 hour response\n• High: 4 hours response\n• Normal: 24 hours response\n• Low: 48 hours response" }
    ]
  },
  {
    id: "IT-SFT-001",
    title: "Approved Software List",
    category: "IT Support",
    sensitivity: "Internal",
    version: "5.1",
    description: "List of software approved for installation on corporate devices.",
    sections: [
      { title: "1. Productivity", content: "Microsoft Office 365, Google Workspace, Slack, Zoom." },
      { title: "2. Development Tools", content: "Visual Studio Code, JetBrains Suite, Docker Desktop, Postman." },
      { title: "3. Requesting New Software", content: "Submit a software approval request via the IT Portal. Approval takes up to 5 business days." }
    ]
  }
];
