import React from 'react';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const FinanceResource = () => {
  return (
    <ResourceView 
      pageName="Finance Reports" 
      fetchFn={resourceService.getFinanceResource} 
    />
  );
};

export default FinanceResource;
