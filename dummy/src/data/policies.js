export const POLICIES = [
  {
    id: "POL-SEC-001",
    title: "Information Security Policy",
    category: "Information Security",
    sensitivity: "Internal",
    version: "2.1",
    lastUpdated: "August 2026",
    owner: "Information Security Department",
    status: "Active",
    sections: [
      { title: "1. Purpose", content: "This policy establishes basic information-security requirements for protecting company systems, applications, and business information." },
      { title: "2. Scope", content: "This policy applies to employees and authorized users accessing company systems and resources." },
      { title: "3. Security Requirements", content: "• Use company accounts only for authorized activities.\n• Protect passwords and authentication information.\n• Access information according to assigned responsibilities.\n• Report suspicious security activity to the appropriate team.\n• Do not share confidential company information with unauthorized users." },
      { title: "4. User Responsibilities", content: "Users are responsible for following company security policies and reporting suspected security incidents promptly." },
      { title: "5. Policy Review", content: "This policy is reviewed periodically by the Information Security Department." }
    ]
  },
  {
    id: "POL-SEC-002",
    title: "Acceptable Use Policy",
    category: "Information Technology",
    sensitivity: "Internal",
    version: "1.5",
    lastUpdated: "January 2026",
    owner: "IT Operations",
    status: "Active",
    sections: [
      { title: "1. Purpose", content: "To outline the acceptable use of computer equipment and networks." },
      { title: "2. Scope", content: "Applies to all employees, contractors, and consultants." },
      { title: "3. Key Requirements", content: "• Systems must be used for legitimate business purposes.\n• Do not install unauthorized software.\n• Do not use systems for illegal activities." }
    ]
  },
  {
    id: "POL-SEC-003",
    title: "Data Protection Policy",
    category: "Compliance",
    sensitivity: "Confidential",
    version: "3.0",
    lastUpdated: "May 2026",
    owner: "Data Privacy Office",
    status: "Active",
    sections: [
      { title: "1. Purpose", content: "To ensure personal data is handled securely and in compliance with privacy laws." },
      { title: "2. Scope", content: "Applies to all processing of personal data." },
      { title: "3. Key Requirements", content: "• Data must be encrypted at rest and in transit.\n• Access is restricted on a least-privilege basis.\n• Report data breaches within 24 hours." }
    ]
  },
  {
    id: "POL-HR-001",
    title: "Remote Work Policy",
    category: "Human Resources",
    sensitivity: "Internal",
    version: "1.2",
    lastUpdated: "March 2026",
    owner: "Human Resources",
    status: "Active",
    sections: [
      { title: "1. Purpose", content: "Guidelines for eligible employees working remotely." },
      { title: "2. Scope", content: "Full-time and part-time remote employees." },
      { title: "3. Key Requirements", content: "• Maintain a secure home network.\n• Use the corporate VPN for access.\n• Ensure availability during core working hours." }
    ]
  }
];
