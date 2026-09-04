import React from 'react';
import UnavailableState from '../../components/dashboard/UnavailableState';

const UnavailablePage = ({ title, message }) => {
  return <UnavailableState title={title} message={message} />;
};

export default UnavailablePage;
