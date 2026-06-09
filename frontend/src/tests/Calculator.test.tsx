import { render, screen, fireEvent } from '@testing-library/react';
import { describe, test, expect } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { Calculator } from '../pages/Calculator';

describe('Calculator Component', () => {
  test('renders step 1 inputs and moves to step 2 on clicking continue', () => {
    render(
      <MemoryRouter>
        <Calculator />
      </MemoryRouter>
    );

    // Assert step 1 heading
    expect(screen.getByRole('heading', { name: /transportation/i })).toBeInTheDocument();
    
    // Assert step 1 fields are visible
    expect(screen.getByLabelText(/car distance/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/bicycle distance/i)).toBeInTheDocument();

    // Move to step 2
    const nextBtn = screen.getByRole('button', { name: /continue/i });
    fireEvent.click(nextBtn);

    // Assert step 2 heading and fields
    expect(screen.getByRole('heading', { name: /energy & diet/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/electricity usage/i)).toBeInTheDocument();
  });
});
