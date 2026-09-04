import React, { useState } from 'react';
import './common.css';

const Input = ({ label, id, error, type, ...props }) => {
  const [showPassword, setShowPassword] = useState(false);
  
  const isPasswordType = type === 'password';
  const inputType = isPasswordType ? (showPassword ? 'text' : 'password') : type;

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="input-group">
      {label && <label htmlFor={id} className="input-label">{label}</label>}
      
      <div className="input-wrapper">
        <input 
          id={id} 
          type={inputType}
          className={`input-field ${error ? 'input-error' : ''} ${isPasswordType ? 'input-with-toggle' : ''}`} 
          {...props} 
        />
        
        {isPasswordType && (
          <button 
            type="button" 
            className="password-toggle-btn" 
            onClick={togglePasswordVisibility}
            aria-label={showPassword ? "Hide password" : "Show password"}
          >
            {showPassword ? "Hide" : "Show"}
          </button>
        )}
      </div>
      
      {error && <span className="error-message">{error}</span>}
    </div>
  );
};

export default Input;
