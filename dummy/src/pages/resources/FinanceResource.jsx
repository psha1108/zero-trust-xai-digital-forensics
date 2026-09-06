import React from 'react';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';
import { FINANCE_DATA } from '../../data/financeData';

const FinanceResource = () => {
  return (
    <ResourceView pageName="Finance" fetchFn={resourceService.getFinanceResource}>
      <div style={{ padding: '10px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
          <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
            <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px', marginTop: 0 }}>Payroll Information</h3>
            <p><strong>Employee ID:</strong> {FINANCE_DATA.payrollInfo.employeeId}</p>
            <p><strong>Pay Period:</strong> {FINANCE_DATA.payrollInfo.payPeriod}</p>
            <p><strong>Status:</strong> <span style={{ color: 'green' }}>{FINANCE_DATA.payrollInfo.status}</span></p>
          </div>
          <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
            <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px', marginTop: 0 }}>Expense Overview</h3>
            <p><strong>Travel Expenses:</strong> {FINANCE_DATA.expenseOverview.travelExpenses}</p>
            <p><strong>Office Expenses:</strong> {FINANCE_DATA.expenseOverview.officeExpenses}</p>
            <p><strong>Learning Expenses:</strong> {FINANCE_DATA.expenseOverview.learningExpenses}</p>
            <p><strong>Pending Reimbursement:</strong> <span style={{ color: '#d97706', fontWeight: 'bold' }}>{FINANCE_DATA.expenseOverview.pendingReimbursement}</span></p>
          </div>
        </div>

        <div style={{ border: '1px solid #ddd', padding: '15px', borderRadius: '5px' }}>
          <h3 style={{ borderBottom: '1px solid #eee', paddingBottom: '10px', marginTop: 0 }}>Financial Documents</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {FINANCE_DATA.financialDocuments.map(doc => (
              <div key={doc.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px', backgroundColor: '#f9f9f9', borderRadius: '4px' }}>
                <span>{doc.title}</span>
                <span style={{ color: '#666', fontSize: '0.9em' }}>{doc.id}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </ResourceView>
  );
};

export default FinanceResource;
