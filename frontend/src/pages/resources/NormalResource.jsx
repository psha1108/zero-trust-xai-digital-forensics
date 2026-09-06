import React from 'react';
import ResourceView from '../../components/resources/ResourceView';
import resourceService from '../../services/resourceService';

const NormalResource = () => {
  return (
    <ResourceView 
      pageName="General Documents" 
      fetchFn={resourceService.getNormalResource} 
    />
  );
};

export default NormalResource;
