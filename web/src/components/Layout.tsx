// web/src/components/Layout.tsx
import React from 'react';

const Layout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div style={{ display: 'flex', fontFamily: 'sans-serif' }}>
      <nav style={{ width: '220px', borderRight: '1px solid #ccc', padding: '20px', height: '100vh' }}>
        <h2>Platform</h2>
        <ul style={{ listStyle: 'none', padding: 0 }}>
          <li style={{ marginBottom: '10px' }}>Dashboard</li>
          <li style={{ marginBottom: '10px', fontWeight: 'bold' }}>Agent Marketplace</li>
          <li style={{ marginBottom: '10px' }}>Workflows</li>
        </ul>
      </nav>
      <main style={{ flex: 1, padding: '20px' }}>
        {children}
      </main>
    </div>
  );
};

export default Layout;
