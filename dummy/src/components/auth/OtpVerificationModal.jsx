import React, { useState, useEffect } from 'react';
import axiosInstance from '../../api/axios';
import './OtpVerificationModal.css';

const OtpVerificationModal = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingCallbacks, setPendingCallbacks] = useState(null);
  
  const [timeLeft, setTimeLeft] = useState(300);
  const [resendCooldown, setResendCooldown] = useState(60);

  useEffect(() => {
    const handleOtpRequired = (event) => {
      setPendingCallbacks(event.detail);
      setIsOpen(true);
      setOtpCode('');
      setError('');
      setTimeLeft(300);
      setResendCooldown(60);
    };

    window.addEventListener('otp_required', handleOtpRequired);

    return () => {
      window.removeEventListener('otp_required', handleOtpRequired);
    };
  }, []);

  useEffect(() => {
    let timer;
    if (isOpen && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isOpen, timeLeft]);

  useEffect(() => {
    let timer;
    if (isOpen && resendCooldown > 0) {
      timer = setInterval(() => {
        setResendCooldown((prev) => prev - 1);
      }, 1000);
    }
    return () => clearInterval(timer);
  }, [isOpen, resendCooldown]);

  const handleVerify = async () => {
    if (!otpCode || otpCode.length !== 6) {
      setError('Please enter a 6-digit verification code.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await axiosInstance.post('/auth/otp/verify', {
        otp_code: otpCode,
      });

      if (response.data.verified) {
        setIsOpen(false);

        if (pendingCallbacks?.onVerify) {
          await pendingCallbacks.onVerify();
        }

        setPendingCallbacks(null);
      }
    } catch (err) {
      if (
        err.response &&
        err.response.data &&
        err.response.data.error
      ) {
        setError(err.response.data.error);
      } else {
        setError('Verification failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setLoading(true);
    setError('');
    
    try {
      await axiosInstance.post('/auth/otp/resend');
      setTimeLeft(300);
      setResendCooldown(60);
      setError('A new code has been sent.');
    } catch (err) {
      if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError('Failed to resend code.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async () => {
    setIsOpen(false);
    
    try {
      await axiosInstance.post('/auth/otp/cancel');
    } catch (err) {
      console.error("Failed to cancel OTP challenge", err);
    }

    if (pendingCallbacks?.onCancel) {
      pendingCallbacks.onCancel();
    }

    setPendingCallbacks(null);
  };

  if (!isOpen) return null;

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="otp-modal-overlay">
      <div className="otp-modal">
        <h2>Additional Verification Required</h2>

        <p>Please verify your identity to continue.</p>
        
        <p className="otp-timer">Code expires in: {formatTime(timeLeft)}</p>

        {error && (
          <div className="otp-error">
            {error}
          </div>
        )}

        <div className="otp-input-group">
          <input
            type="text"
            maxLength={6}
            placeholder="000000"
            value={otpCode}
            onChange={(e) =>
              setOtpCode(
                e.target.value.replace(/[^0-9]/g, '')
              )
            }
            disabled={loading || timeLeft === 0}
            autoFocus
          />
        </div>

        <div className="otp-actions" style={{ flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
            <button
              onClick={handleCancel}
              disabled={loading}
              className="btn-cancel"
            >
              Cancel
            </button>

            <button
              onClick={handleVerify}
              disabled={
                loading || otpCode.length !== 6 || timeLeft === 0
              }
              className="btn-verify"
            >
              {loading ? 'Verifying...' : 'Verify'}
            </button>
          </div>
          
          <button 
            onClick={handleResend} 
            disabled={loading || resendCooldown > 0}
            className="btn-resend"
            style={{ background: 'none', border: 'none', color: '#0066cc', cursor: 'pointer', textDecoration: 'underline' }}
          >
            {resendCooldown > 0 ? `Resend code in ${resendCooldown}s` : 'Resend code'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OtpVerificationModal;