import React, {
  useEffect,
  useState,
} from 'react';

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

  if (response?.status === 403) {
    return (
      'Your account does not have the required permissions to access this resource.'
    );
  }

  if (response?.status === 401) {
    return (
      'Your current session cannot access this resource.'
    );
  }

  return 'The requested company resource could not be loaded.';
};

const ResourceView = ({
  fetchFn,
  pageName,
  subtitle,
  children,
}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [otpRequired, setOtpRequired] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [otpError, setOtpError] = useState('');
  const [otpLoading, setOtpLoading] = useState(false);

  const loadResource = async () => {
    setLoading(true);
    setError('');

    try {
      const responseData = await fetchFn();

      setData(responseData);
      setOtpRequired(false);
      setOtpCode('');
      setOtpError('');
    } catch (err) {
      setData(null);

      if (isOtpChallenge(err)) {
        setError('');
        setOtpRequired(true);
        setOtpError('');
      } else {
        setOtpRequired(false);
        setError(getErrorMessage(err));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let active = true;

    const start = async () => {
      try {
        const responseData = await fetchFn();

        if (!active) {
          return;
        }

        setData(responseData);
        setOtpRequired(false);
        setOtpCode('');
        setOtpError('');
        setError('');
      } catch (err) {
        if (!active) {
          return;
        }

        setData(null);

        if (isOtpChallenge(err)) {
          setError('');
          setOtpRequired(true);
          setOtpError('');
        } else {
          setOtpRequired(false);
          setError(getErrorMessage(err));
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    start();

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
      setOtpError(
        'Enter the 6-digit verification code.'
      );
      return;
    }

    setOtpLoading(true);
    setOtpError('');
    setError('');

    try {
      const verification =
        await authService.verifyOtp(otpCode);

      if (verification?.verified !== true) {
        setOtpError(
          'Verification could not be completed.'
        );
        return;
      }

      await loadResource();
    } catch (err) {
      setOtpError(
        err?.response?.data?.error ||
        'Verification could not be completed.'
      );
    } finally {
      setOtpLoading(false);
    }
  };

  return (
    <div className="resource-view-container">
      <div className="page-heading-block">
        <p className="page-eyebrow">
          ACME Technologies
        </p>

        <h1 className="page-title">
          {pageName}
        </h1>

        {subtitle && (
          <p className="page-subtitle">
            {subtitle}
          </p>
        )}
      </div>

      {loading ? (
        <Card>
          <div className="placeholder-text">
            Loading company resource...
          </div>
        </Card>
      ) : otpRequired ? (
        <Card>
          <div
            className="otp-step-up"
            aria-live="polite"
          >
            <h2 className="resource-title">
              Additional Verification Required
            </h2>

            <p className="resource-message">
              Please complete the one-time verification
              step to continue to this company resource.
            </p>

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
                6-digit verification code
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
                  : 'Continue'}
              </button>
            </form>
          </div>
        </Card>
      ) : error ? (
        <Card>
          <div
            className="business-access-denied"
            role="alert"
          >
            <h2>
              Access Restricted
            </h2>

            <p>
              {error}
            </p>

            <p className="muted-text">
              If you believe you require access,
              contact your department administrator.
            </p>
          </div>
        </Card>
      ) : data ? (
        <>
          {children || (
            <Card title={data.title}>
              <p>
                {data.message}
              </p>
            </Card>
          )}
        </>
      ) : null}
    </div>
  );
};

export default ResourceView;
