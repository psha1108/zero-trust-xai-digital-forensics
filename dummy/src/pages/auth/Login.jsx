import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import authService from '../../services/authService';
import Input from '../../components/common/Input';
import Button from '../../components/common/Button';
import './Auth.css';

const Login = () => {
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [requireOtp, setRequireOtp] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [tempUser, setTempUser] = useState(null);

  const navigate = useNavigate();
  const { login, setUser } = useAuth(); 

  const handleChange = (e) => {
    const { id, value } = e.target;
    setFormData((prev) => ({ ...prev, [id]: value }));
    if (error) setError('');
  };

  const handleOtpChange = (e) => {
    setOtpCode(e.target.value);
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (requireOtp) {
      if (!otpCode || otpCode.length !== 6) {
        setError('Please enter a 6-digit OTP.');
        return;
      }
      setIsLoading(true);
      try {
        const data = await authService.verifyOtp(otpCode);
        if (data.verified) {
          setUser(tempUser);
          navigate('/dashboard', { replace: true });
        }
      } catch (err) {
        if (err.response && err.response.data && err.response.data.error) {
          setError(err.response.data.error);
        } else {
          setError('OTP verification failed.');
        }
      } finally {
        setIsLoading(false);
      }
      return;
    }

    const trimmedUsername = formData.username.trim();
    
    if (!trimmedUsername || !formData.password) {
      setError('Please fill in all fields.');
      return;
    }

    setIsLoading(true);
    try {
      const data = await login(trimmedUsername, formData.password);
      if (data.require_otp) {
        setRequireOtp(true);
        setTempUser(data.user);
      } else {
        navigate('/dashboard', { replace: true });
      }
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
          <h1 className="auth-title">Zero Trust Auth</h1>
          <p className="auth-subtitle">
            {requireOtp ? 'Step-up Authentication' : 'Secure Gateway Access'}
          </p>
        </div>
        
        {error && <div className="auth-error" role="alert">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          {!requireOtp ? (
            <>
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
            </>
          ) : (
            <Input 
              label="OTP Code" 
              id="otpCode" 
              type="text" 
              placeholder="Enter 6-digit OTP"
              value={otpCode}
              onChange={handleOtpChange}
              aria-invalid={!!error}
            />
          )}
          
          <Button type="submit" isLoading={isLoading} aria-live="polite">
            {requireOtp ? 'Verify OTP' : 'Authenticate'}
          </Button>
        </form>

        {!requireOtp && (
          <div className="auth-footer">
            Don't have an access clearance? 
            <Link to="/register" className="auth-link">Register</Link>
          </div>
        )}
      </div>
    </div>
  );
};

export default Login;
