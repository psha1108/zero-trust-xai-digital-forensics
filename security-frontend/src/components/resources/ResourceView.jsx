import React, { useEffect, useState } from 'react';
import Card from '../dashboard/Card';
import authService from '../../services/authService';
import './ResourceView.css';

const isOtpChallenge = (err) => {
  const response = err?.response;
  const payload = response?.data;

  return (
    response?.status === 401 &&
    payload?.requires_otp === true &&
    payload?.policy_action === 'OTP'
  );
};

const getErrorMessage = (err) => {
  const response = err?.response;
  const payload = response?.data;

  if (response?.status === 403) {
    return (
      payload?.error ||
      '403 Forbidden: You do not have clearance to access this resource.'
    );
  }

  if (payload?.error) {
    return payload.error;
  }

  return 'Secure connection failed. Unable to retrieve resource.';
};

const ResourceView = ({ fetchFn, pageName }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [otpRequired, setOtpRequired] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [otpError, setOtpError] = useState('');
  const [otpLoading, setOtpLoading] = useState(false);

  useEffect(() => {
    let active = true;

    const loadResource = async () => {
      setLoading(true);
      setError('');

      try {
        const responseData = await fetchFn();

        if (!active) {
          return;
        }

        setData(responseData);
        setOtpRequired(false);
        setOtpCode('');
        setOtpError('');
      } catch (err) {
        if (!active) {
          return;
        }

        if (isOtpChallenge(err)) {
          setData(null);
          setError('');
          setOtpRequired(true);
          setOtpError('');
        } else {
          setData(null);
          setOtpRequired(false);
          setError(getErrorMessage(err));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadResource();

    return () => {
      active = false;
    };
  }, [fetchFn]);

  const handleOtpChange = (event) => {
    const numericValue = event.target.value
      .replace(/\D/g, '')
      .slice(0, 6);

    setOtpCode(numericValue);

    if (otpError) {
      setOtpError('');
    }
  };

  const handleOtpSubmit = async (event) => {
    event.preventDefault();

    if (!/^\d{6}$/.test(otpCode)) {
      setOtpError('Enter the 6-digit OTP.');
      return;
    }

    setOtpLoading(true);
    setOtpError('');
    setError('');

    let verification;

    try {
      verification = await authService.verifyOtp(otpCode);
    } catch (err) {
      setOtpError(
        err?.response?.data?.error ||
        'OTP verification failed.'
      );
      setOtpLoading(false);
      return;
    }

    if (verification?.verified !== true) {
      setOtpError('OTP verification failed.');
      setOtpLoading(false);
      return;
    }

    try {
      // Retry the exact protected resource. Flask remains responsible
      // for re-running ML analysis and Zero Trust policy enforcement.
      const responseData = await fetchFn();

      setData(responseData);
      setOtpRequired(false);
      setOtpCode('');
      setOtpError('');
      setError('');
    } catch (err) {
      setData(null);

      if (isOtpChallenge(err)) {
        setOtpRequired(true);
        setOtpError(
          err?.response?.data?.error ||
          'OTP verification is still required.'
        );
      } else {
        // A verified OTP must never override Restrict or Block.
        setOtpRequired(false);
        setError(getErrorMessage(err));
      }
    } finally {
      setOtpLoading(false);
    }
  };

  return (
    <div className="resource-view-container">
      <h1 className="page-title">{pageName}</h1>

      <Card>
        {loading ? (
          <div className="placeholder-text">
            Establishing secure connection...
          </div>
        ) : otpRequired ? (
          <div className="otp-step-up" aria-live="polite">
            <div className="otp-step-up-header">
              <h2 className="resource-title">
                Additional Verification Required
              </h2>

              <p className="resource-message">
                Zero Trust policy requires a one-time password before
                this resource can be accessed.
              </p>
            </div>

            {otpError && (
              <div
                className="otp-error"
                role="alert"
              >
                {otpError}
              </div>
            )}

            <form
              className="otp-form"
              onSubmit={handleOtpSubmit}
            >
              <label
                className="otp-label"
                htmlFor="otpCode"
              >
                6-digit OTP
              </label>

              <input
                id="otpCode"
                name="otpCode"
                className="otp-input"
                type="text"
                inputMode="numeric"
                pattern="[0-9]{6}"
                maxLength={6}
                autoComplete="one-time-code"
                value={otpCode}
                onChange={handleOtpChange}
                disabled={otpLoading}
                aria-invalid={Boolean(otpError)}
                aria-describedby={
                  otpError
                    ? 'otp-error-message'
                    : undefined
                }
                placeholder="000000"
              />

              <button
                className="otp-submit"
                type="submit"
                disabled={
                  otpLoading ||
                  otpCode.length !== 6
                }
              >
                {otpLoading
                  ? 'Verifying...'
                  : 'Verify OTP'}
              </button>
            </form>

            {otpError && (
              <span
                id="otp-error-message"
                className="sr-only"
              >
                {otpError}
              </span>
            )}
          </div>
        ) : error ? (
          <div
            className="placeholder-text error-text"
            role="alert"
          >
            {error}
          </div>
        ) : data ? (
          <div className="resource-data">
            <h2 className="resource-title">
              {data.title}
            </h2>

            <div className="resource-meta">
              <span className="status-label">
                Classification:
              </span>

              <span
                className={
                  `status-value uppercase sensitivity-${data.sensitivity}`
                }
              >
                {data.sensitivity}
              </span>
            </div>

            <p className="resource-message">
              {data.message}
            </p>
          </div>
        ) : null}
      </Card>
    </div>
  );
};

export default ResourceView;
