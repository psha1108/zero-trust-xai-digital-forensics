import React, {
  useEffect,
  useState,
} from 'react';

import Card from '../../components/dashboard/Card';
import portalService from '../../services/portalService';

const formatTime = (value) => {
  if (!value) {
    return 'Unavailable';
  }

  const parsed = new Date(value);

  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleString();
};

const MySessions = () => {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    const loadSession = async () => {
      try {
        const data =
          await portalService.getCurrentSession();

        if (active) {
          setSession(data);
        }
      } catch {
        if (active) {
          setError(
            'Current session information could not be loaded.'
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadSession();

    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="dashboard-container">
      <div className="page-heading-block">
        <p className="page-eyebrow">
          Account
        </p>

        <h1 className="page-title">
          My Sessions
        </h1>

        <p className="page-subtitle">
          Review your current corporate portal session.
        </p>
      </div>

      <Card title="Current Session">
        {loading ? (
          <p>
            Loading session information...
          </p>
        ) : error ? (
          <p className="error-text">
            {error}
          </p>
        ) : (
          <div className="profile-detail-grid">
            <div>
              <span className="profile-label">
                User
              </span>

              <strong>
                {session?.username || 'Unavailable'}
              </strong>
            </div>

            <div>
              <span className="profile-label">
                Status
              </span>

              <strong className="positive-text">
                {session?.is_active
                  ? 'Active'
                  : 'Inactive'}
              </strong>
            </div>

            <div>
              <span className="profile-label">
                Login Time
              </span>

              <strong>
                {formatTime(session?.started_at)}
              </strong>
            </div>

            <div>
              <span className="profile-label">
                Current IP
              </span>

              <strong>
                {session?.current_ip || 'Unavailable'}
              </strong>
            </div>

            <div>
              <span className="profile-label">
                Device
              </span>

              <strong>
                Windows workstation
              </strong>
            </div>

            <div>
              <span className="profile-label">
                Browser
              </span>

              <strong>
                Chrome
              </strong>
            </div>
          </div>
        )}
      </Card>

      <p className="demo-data-note">
        Session status, login time and network information
        are retrieved from the real project backend.
        Friendly device labels are demonstration presentation data.
      </p>
    </div>
  );
};

export default MySessions;
