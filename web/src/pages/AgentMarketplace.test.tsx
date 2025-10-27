// web/src/pages/AgentMarketplace.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import AgentMarketplace from './AgentMarketplace';

// Mock the global fetch function
global.fetch = vi.fn();

function createFetchResponse(data: any) {
  return { json: () => new Promise((resolve) => resolve(data)), ok: true }
}

describe('AgentMarketplace', () => {
  it('renders the main heading after data fetching', async () => {
    const mockAgents = [{ id: '1', name: 'Test Agent', description: 'A test agent', category: 'Testing' }];
    (fetch as jest.Mock).mockResolvedValue(createFetchResponse(mockAgents));

    render(<AgentMarketplace />);

    // Wait for the heading to appear after the loading is done
    await waitFor(() => {
        expect(screen.getByRole('heading', { name: /agent marketplace/i })).toBeInTheDocument();
    });
  });

  it('shows a loading state initially', () => {
    render(<AgentMarketplace />);
    expect(screen.getByText(/loading agents.../i)).toBeInTheDocument();
  });

  it('displays agents after data fetching', async () => {
    const mockAgents = [
        { id: '1', name: 'Test Agent 1', description: 'First agent', category: 'Testing' },
        { id: '2', name: 'Test Agent 2', description: 'Second agent', category: 'General' },
    ];
    (fetch as jest.Mock).mockResolvedValue(createFetchResponse(mockAgents));

    render(<AgentMarketplace />);

    // Wait for the agent names to appear
    await waitFor(() => {
        expect(screen.getByText('Test Agent 1')).toBeInTheDocument();
        expect(screen.getByText('Test Agent 2')).toBeInTheDocument();
    });

    // Ensure the loading message is gone
    expect(screen.queryByText(/loading agents.../i)).not.toBeInTheDocument();
  });
});
