import React from 'react';
import Card from '../../components/dashboard/Card';

const NormalResource = () => {
  return (
    <div>
      <h1 className="page-title">Normal Resource Access</h1>
      <Card>
        <div className="placeholder-text">Resource data will load here based on backend API.</div>
      </Card>
    </div>
  );
};

export default NormalResource;
