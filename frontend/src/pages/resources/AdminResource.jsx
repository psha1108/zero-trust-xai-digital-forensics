import React from 'react';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const AdminResource = () => {
  return (
    <ResourceView 
      pageName="Admin Controls" 
      fetchFn={resourceService.getAdminResource} 
    />
  );
};

export default AdminResource;
