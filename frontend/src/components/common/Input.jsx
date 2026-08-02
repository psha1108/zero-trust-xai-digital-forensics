import React from 'react';
import './common.css'; // We'll create this for shared component styles

const Input = ({ label, id, error, ...props }) => {
  return (
    <div className="input-group">
      {label && <label htmlFor={id} className="input-label">{label}</label>}
      <input id={id} className={`input-field ${error ? 'input-error' : ''}`} {...props} />
      {error && <span className="error-message">{error}</span>}
    </div>
  );
};

export default Input;
