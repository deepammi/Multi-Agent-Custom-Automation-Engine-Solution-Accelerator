import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';

// Simple component to test
const SimpleComponent = ({ text }: { text: string }) => {
  return <div>{text}</div>;
};

describe('Simple Test', () => {
  it('should render a simple component', () => {
    render(<SimpleComponent text="Hello World" />);
    expect(screen.getByText('Hello World')).toBeInTheDocument();
  });
});