// web/src/pages/AgentMarketplace.tsx
import { useState, useEffect } from 'react';

interface Agent {
  id: string;
  name: string;
  description: string;
  category: string;
}

const API_BASE_URL = 'http://localhost:5000'; // Should be in an env file in a real app

const AgentMarketplace = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/agents/library`);
        if (!response.ok) {
          throw new Error('Failed to fetch agents');
        }
        const data: Agent[] = await response.json();
        setAgents(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchAgents();
  }, []);

  if (loading) {
    return <div>Loading agents...</div>;
  }

  if (error) {
    return <div style={{ color: 'red' }}>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Agent Marketplace</h1>
      <p>Discover and select from our library of AI agents to build your automations.</p>

      <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap', marginTop: '30px' }}>
        {agents.map(agent => (
          <div key={agent.id} style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '20px', width: '300px' }}>
            <h3 style={{ marginTop: 0 }}>{agent.name}</h3>
            <p style={{ fontSize: '14px', color: '#555' }}>{agent.description}</p>
            <span style={{ background: '#eee', padding: '5px 10px', borderRadius: '12px', fontSize: '12px' }}>
              {agent.category}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AgentMarketplace;
