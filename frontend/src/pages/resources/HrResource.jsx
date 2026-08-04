import React from 'react';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const HrResource = () => {
  return (
    <ResourceView 
      pageName="HR Resource Access" 
      fetchFn={resourceService.getHrResource} 
    />
  );
};

export default HrResource;
