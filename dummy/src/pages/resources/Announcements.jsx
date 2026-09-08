import React, { useState } from 'react';
import Card from '../../components/dashboard/Card';
import { ANNOUNCEMENTS } from '../../data/announcements';

const AnnouncementsList = ({ announcements, onSelect }) => {
  return (
    <div className="resource-grid">
      {announcements.map(ann => (
        <div key={ann.id} className="resource-card-container">
          <Card className="resource-card-content">
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <h3 style={{ margin: 0, fontSize: '1.1em', paddingRight: '10px' }}>{ann.title}</h3>
              </div>
              <p style={{ margin: '0 0 15px 0', color: 'var(--text-secondary)', fontSize: '0.9em', flexGrow: 1 }}>
                {ann.summary}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85em', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                <span>Published: {ann.published}</span>
              </div>
              <div style={{ fontSize: '0.8em', color: '#999', borderTop: '1px solid var(--border-color)', paddingTop: '10px', marginTop: '10px' }}>
                Announcement ID: {ann.id}
              </div>
              <button className="resource-btn" onClick={() => onSelect(ann)}>VIEW</button>
            </div>
          </Card>
        </div>
      ))}
    </div>
  );
};

const AnnouncementDetails = ({ ann, onBack }) => {
  return (
    <div>
      <button className="resource-btn-back" onClick={onBack}>
        &larr; BACK TO ANNOUNCEMENTS
      </button>
      <Card>
        <div style={{ padding: '20px' }}>
          <h2 style={{ marginTop: 0, marginBottom: '10px', color: 'var(--primary-color)' }}>{ann.title}</h2>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '20px', display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
            <span><strong>ID:</strong> {ann.id}</span>
            <span><strong>Department:</strong> {ann.department}</span>
            <span><strong>Published:</strong> {ann.published}</span>
          </div>

          <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px', marginBottom: '20px' }}>
            <p style={{ lineHeight: '1.6', fontSize: '1.05em' }}>{ann.message}</p>
          </div>

          {ann.additionalInformation && (
            <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '20px', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
              <p style={{ margin: 0 }}>{ann.additionalInformation}</p>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

const Announcements = () => {
  const [selectedAnnouncement, setSelectedAnnouncement] = useState(null);

  return (
    <div className="resource-view-container">
      <h1 className="page-title">Announcements</h1>
      {selectedAnnouncement ? (
        <AnnouncementDetails ann={selectedAnnouncement} onBack={() => setSelectedAnnouncement(null)} />
      ) : (
        <div>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px' }}>Latest company news and department announcements.</p>
          <AnnouncementsList announcements={ANNOUNCEMENTS} onSelect={setSelectedAnnouncement} />
        </div>
      )}
    </div>
  );
};

export default Announcements;
