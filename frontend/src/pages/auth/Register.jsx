import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import authService from '../../services/authService';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import './Auth.css';

const Register = () => {
  const [formData, setFormData] = useState({ username: '', email: '', password: '', confirmPassword: '' });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const validators = {
    username: (value) => {
      if (!value) return 'Username is required.';
      if (!/^[a-zA-Z][a-zA-Z0-9_]{3,19}$/.test(value)) {
        return 'Username must be 4-20 chars, start with a letter, and contain only letters, numbers, or underscores.';
      }
      return '';
    },
    email: (value) => {
      if (!value) return 'Email is required.';
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        return 'Please enter a valid email address.';
      }
      return '';
    },
    password: (value) => {
      if (!value) return 'Password is required.';
      if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$/.test(value)) {
        return 'Password must be at least 8 chars, with 1 uppercase, 1 lowercase, 1 digit, and 1 special character.';
      }
      return '';
    },
    confirmPassword: (value, form) => {
      if (!value) return 'Please confirm your password.';
      if (value !== form.password) {
        return 'Passwords do not match.';
      }
      return '';
    }
  };

  const handleChange = (e) => {
    const { id, value } = e.target;
    setFormData((prev) => ({ ...prev, [id]: value }));
    // Clear specific field error when typing
    if (errors[id]) {
      setErrors((prev) => ({ ...prev, [id]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    let isValid = true;
    
    // Trim values for validation
    const trimmedData = {
      ...formData,
      username: formData.username.trim(),
      email: formData.email.trim()
    };

    Object.keys(validators).forEach(key => {
      const errorMsg = validators[key](trimmedData[key], trimmedData);
      if (errorMsg) {
        newErrors[key] = errorMsg;
        isValid = false;
      }
    });

    setErrors(newErrors);
    return { isValid, trimmedData };
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setServerError('');
    
    const { isValid, trimmedData } = validateForm();
    if (!isValid) return;

    setIsLoading(true);
    try {
      const payload = {
        username: trimmedData.username,
        email: trimmedData.email,
        password: formData.password // Don't trim password
      };
      
      await authService.register(payload);
      navigate('/login', { replace: true, state: { message: 'Registration successful. Please login.' } });
    } catch (err) {
      if (err.response && err.response.data && err.response.data.message) {
        setServerError(err.response.data.message);
      } else if (err.response && err.response.data && err.response.data.error) {
        setServerError(err.response.data.error);
      } else if (err.response && err.response.status === 409) {
        setServerError('Username or email already exists.');
      } else {
        setServerError('Registration failed securely. Please verify your details and try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1 className="auth-title">Create Portal Account</h1>
          <p className="auth-subtitle">Register for Corporate Portal Access</p>
        </div>
        
        {serverError && <div className="auth-error" role="alert">{serverError}</div>}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <Input 
            label="Username" 
            id="username" 
            type="text" 
            placeholder="Choose a username"
            value={formData.username}
            onChange={handleChange}
            error={errors.username}
            aria-invalid={!!errors.username}
          />
          
          <Input 
            label="Email" 
            id="email" 
            type="email" 
            placeholder="Enter your email address"
            value={formData.email}
            onChange={handleChange}
            error={errors.email}
            aria-invalid={!!errors.email}
          />
          
          <Input 
            label="Password" 
            id="password" 
            type="password" 
            placeholder="Create a strong password"
            value={formData.password}
            onChange={handleChange}
            error={errors.password}
            aria-invalid={!!errors.password}
          />

          <Input 
            label="Confirm Password" 
            id="confirmPassword" 
            type="password" 
            placeholder="Confirm your password"
            value={formData.confirmPassword}
            onChange={handleChange}
            error={errors.confirmPassword}
            aria-invalid={!!errors.confirmPassword}
          />
          
          <Button type="submit" isLoading={isLoading} aria-live="polite">
            Enroll Device
          </Button>
        </form>

        <div className="auth-footer">
          Already have an account? 
          <Link to="/login" className="auth-link">Login</Link>
        </div>
      </div>
    </div>
  );
};

export default Register;
