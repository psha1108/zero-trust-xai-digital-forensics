import React, { useState, useEffect } from 'react';
import axiosInstance from '../../api/axios';
import './OtpVerificationModal.css';

const OtpVerificationModal = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingCallbacks, setPendingCallbacks] = useState(null);

  useEffect(() => {
    const handleOtpRequired = (event) => {
      setPendingCallbacks(event.detail);
      setIsOpen(true);
      setOtpCode('');
      setError('');
    };

    window.addEventListener('otp_required', handleOtpRequired);

    return () => {
      window.removeEventListener('otp_required', handleOtpRequired);
    };
  }, []);

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

  const handleCancel = () => {
    setIsOpen(false);

    if (pendingCallbacks?.onCancel) {
      pendingCallbacks.onCancel();
    }

    setPendingCallbacks(null);
  };

  if (!isOpen) return null;

  return (
    <div className="otp-modal-overlay">
      <div className="otp-modal">
        <h2>Additional Verification Required</h2>

        <p>Please verify your identity to continue.</p>

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
            disabled={loading}
            autoFocus
          />
        </div>

        <div className="otp-actions">
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
              loading || otpCode.length !== 6
            }
            className="btn-verify"
          >
            {loading ? 'Verifying...' : 'Verify'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default OtpVerificationModal;