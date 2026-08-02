import React from 'react';
import './common.css';

const Button = ({ children, type = 'button', variant = 'primary', className = '', isLoading = false, ...props }) => {
  return (
    <button 
      type={type} 
      className={`btn btn-${variant} ${className}`} 
      disabled={isLoading || props.disabled}
      {...props}
    >
      {isLoading ? <span className="spinner"></span> : children}
    </button>
  );
};

export default Button;
