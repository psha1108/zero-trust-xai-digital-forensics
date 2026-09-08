export const DOCUMENTS = [
  {
    id: "DOC-001",
    title: "Employee Handbook",
    description: "Guidelines covering workplace practices, employee responsibilities, benefits, and company procedures.",
    category: "Human Resources",
    status: "Active",
    type: "PDF",
    sensitivity: "Internal",
    lastUpdated: "August 2026",
    sections: [
      { title: "1. Overview", content: "Welcome to the company. This handbook provides an overview of our workplace policies, culture, and what you can expect as an employee." },
      { title: "2. Workplace Conduct", content: "We expect all employees to maintain professional behavior, respect colleagues, and foster an inclusive environment." },
      { title: "3. Benefits & Compensation", content: "Our comprehensive benefits package includes health insurance, retirement plans, and paid time off." }
    ]
  },
  {
    id: "DOC-002",
    title: "Project Architecture Document",
    description: "Technical architecture details for the new deployment.",
    category: "Engineering",
    status: "Active",
    type: "Document",
    sensitivity: "Confidential",
    lastUpdated: "September 2026",
    sections: [
      { title: "1. System Overview", content: "The system implements a modern microservices architecture with a focus on scalability and security." },
      { title: "2. Components", content: "Key components include the API Gateway, Authentication Service, and distributed database cluster." }
    ]
  },
  {
    id: "DOC-003",
    title: "Security Guidelines",
    description: "Best practices for secure development and operations.",
    category: "Information Security",
    status: "Active",
    type: "PDF",
    sensitivity: "Internal",
    lastUpdated: "July 2026",
    sections: [
      { title: "1. Authentication", content: "All internal services must enforce multi-factor authentication (MFA) for access." },
      { title: "2. Data Handling", content: "Customer data must be encrypted at rest and in transit using industry-standard protocols." }
    ]
  },
  {
    id: "DOC-004",
    title: "Quarterly Planning Document",
    description: "Goals and objectives for the upcoming quarter.",
    category: "Management",
    status: "Active",
    type: "Spreadsheet",
    sensitivity: "Internal",
    lastUpdated: "September 2026",
    sections: [
      { title: "1. Objectives", content: "Increase system reliability, improve deployment times, and complete the security audit." },
      { title: "2. Resource Allocation", content: "Engineering teams will focus 80% on core objectives and 20% on technical debt." }
    ]
  }
];
