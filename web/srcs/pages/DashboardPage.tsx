// src/pages/DashboardPage.tsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const DashboardPage = () => {
  const { currentUser, logout } = useAuth();
  const [workflows, setWorkflows] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchWorkflows = async () => {
      try {
        const response = await axios.get('http://localhost:5000/workflows', {
          headers: { 'x-access-token': currentUser.token },
        });
        setWorkflows(response.data);
      } catch (error) {
        console.error('Failed to fetch workflows', error);
      }
    };

    if (currentUser) {
      fetchWorkflows();
    }
  }, [currentUser]);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div>
      <h2>Dashboard</h2>
      <p>Welcome, {currentUser?.username}!</p>
      <button onClick={handleLogout}>Logout</button>
      <h3>Your Workflows</h3>
      <ul>
        {workflows.map((flow) => (
          <li key={flow.id}>{flow.name} - {flow.status}</li>
        ))}
      </ul>
    </div>
  );
};

export default DashboardPage;
