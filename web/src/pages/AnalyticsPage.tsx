// src/pages/AnalyticsPage.tsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

const AnalyticsPage = () => {
  const { currentUser } = useAuth();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const response = await axios.get('http://localhost:5000/analytics/events', {
        headers: { 'x-access-token': currentUser.token },
      });
      setEvents(response.data);
    } catch (error) {
      console.error('Failed to fetch analytics events', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentUser) {
      fetchAnalytics();
    }
  }, [currentUser]);

  return (
    <div>
      <h2>Analytics Dashboard</h2>
      <button onClick={fetchAnalytics} disabled={loading}>
        {loading ? 'Refreshing...' : 'Refresh Data'}
      </button>
      <table>
        <thead>
          <tr>
            <th>Event Type</th>
            <th>Workflow ID</th>
            <th>Agent ID</th>
            <th>Duration (s)</th>
            <th>Status</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.id}>
              <td>{event.event_type}</td>
              <td>{event.workflow_id}</td>
              <td>{event.agent_id}</td>
              <td>{event.duration?.toFixed(2)}</td>
              <td>{event.status}</td>
              <td>{new Date(event.timestamp).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default AnalyticsPage;
