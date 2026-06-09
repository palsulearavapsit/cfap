import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Navbar } from '../components/Navbar';

describe('Navbar Component', () => {
  test('does not render if unauthenticated', () => {
    localStorage.clear();
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument();
  });

  test('renders navigation links and email if authenticated', () => {
    localStorage.setItem('access_token', 'mock_token');
    localStorage.setItem('user_email', 'test@example.com');
    
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );

    expect(screen.getByRole('navigation')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Calculator')).toBeInTheDocument();
    expect(screen.getByText('Challenges')).toBeInTheDocument();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  test('clears localstorage on logout click', () => {
    localStorage.setItem('access_token', 'mock_token');
    localStorage.setItem('user_email', 'test@example.com');

    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>
    );

    const logoutBtn = screen.getByRole('button', { name: /log out/i });
    fireEvent.click(logoutBtn);

    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('user_email')).toBeNull();
  });
});
