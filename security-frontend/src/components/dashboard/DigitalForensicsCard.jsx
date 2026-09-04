import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Card from './Card';
import { useAuth } from '../../hooks/useAuth';
import forensicsService from '../../services/forensicsService';
import { formatDateIST } from '../../utils/dateUtils';

const DigitalForensicsCard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [evidence, setEvidence] = useState([]);
  const [integrity, setIntegrity] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user?.role !== 'admin') {
      return;
    }

    let cancelled = false;

    const loadForensicsSummary = async () => {
      setLoading(true);
      setError(null);

      try {
        const [evidenceData, integrityData] = await Promise.all([
          forensicsService.getEvidence(),
          forensicsService.verifyIntegrity(),
        ]);

        if (cancelled) {
          return;
        }

        setEvidence(
          Array.isArray(evidenceData)
            ? evidenceData
            : []
        );

        setIntegrity(
          integrityData || null
        );
      } catch {
        if (!cancelled) {
          setError(
            'Failed to load Digital Forensics summary.'
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadForensicsSummary();

    return () => {
      cancelled = true;
    };
  }, [user?.role]);

  if (user?.role !== 'admin') {
    return (
      <Card
        title="Digital Forensics"
        className="widget-forensics"
      >
        <div className="status-item">
          <span className="status-label">
            Access
          </span>
          <span className="status-value text-muted">
            Admin access required
          </span>
        </div>
      </Card>
    );
  }

  const latestEvidence = evidence.reduce(
    (latest, current) => {
      if (!current?.created_at) {
        return latest;
      }

      if (!latest?.created_at) {
        return current;
      }

      return (
        new Date(current.created_at) >
        new Date(latest.created_at)
      )
        ? current
        : latest;
    },
    null
  );

  return (
    <Card
      title="Digital Forensics"
      className="widget-forensics"
    >
      {loading ? (
        <div className="placeholder-text">
          Loading forensic evidence...
        </div>
      ) : error ? (
        <div className="placeholder-text">
          {error}
        </div>
      ) : (
        <>
          <div className="status-item">
            <span className="status-label">
              Evidence Records
            </span>
            <span className="status-value">
              {evidence.length}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">
              Evidence Integrity
            </span>
            <span
              className={
                integrity?.status === 'VALID'
                  ? 'status-value success'
                  : 'status-value'
              }
            >
              {integrity?.status || 'Unavailable'}
            </span>
          </div>

          <div className="status-item">
            <span className="status-label">
              Latest Evidence
            </span>
            <span className="status-value text-muted">
              {latestEvidence?.created_at
                ? formatDateIST(
                    latestEvidence.created_at
                  )
                : 'No evidence records'}
            </span>
          </div>

          <div
            style={{
              marginTop: '1rem',
            }}
          >
            <button
              type="button"
              onClick={() => navigate('/forensics')}
            >
              Open Digital Forensics
            </button>
          </div>
        </>
      )}
    </Card>
  );
};

export default DigitalForensicsCard;
