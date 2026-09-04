import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import './Auth.css';

const Login = () => {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { login } = useAuth(); 

  const handleChange = (e) => {
    const { id, value } = e.target;
    setFormData((prev) => ({ ...prev, [id]: value }));
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    const trimmedUsername = formData.username.trim();
    
    if (!trimmedUsername || !formData.password) {
      setError('Please fill in all fields.');
      return;
    }

    setIsLoading(true);
    try {
      await login(trimmedUsername, formData.password);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      if (err.response && err.response.data && err.response.data.message) {
        setError(err.response.data.message);
      } else if (err.response && err.response.data && err.response.data.error) {
        setError(err.response.data.error);
      } else if (err.response && err.response.status === 401) {
        setError('Invalid username or password.');
      } else {
        setError('Login failed securely. Please verify your credentials.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <h1 className="auth-title">AI Security Operations Console</h1>
          <p className="auth-subtitle">Authorized Security Administrator Access</p>
        </div>
        
        {error && <div className="auth-error" role="alert">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          <Input 
            label="Username" 
            id="username" 
            type="text" 
            placeholder="Enter your username"
            value={formData.username}
            onChange={handleChange}
            aria-invalid={!!error}
          />
          
          <Input 
            label="Password" 
            id="password" 
            type="password" 
            placeholder="Enter your password"
            value={formData.password}
            onChange={handleChange}
            aria-invalid={!!error}
          />
          
          <Button type="submit" isLoading={isLoading} aria-live="polite">
            Authenticate
          </Button>
        </form>
      </div>
    </div>
  );
};

export default Login;
