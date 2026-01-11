import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ErrorDisplay from '../components/content/ErrorDisplay';

describe('ErrorDisplay Component', () => {
    it('renders error message and restart button', () => {
        const mockOnRestart = vi.fn();
        const errorMessage = 'Test error message';
        
        render(
            <ErrorDisplay
                message={errorMessage}
                onRestart={mockOnRestart}
            />
        );
        
        // Check if error message is displayed
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
        
        // Check if restart button is displayed
        expect(screen.getByText('Start New Task')).toBeInTheDocument();
    });
    
    it('calls onRestart when restart button is clicked', () => {
        const mockOnRestart = vi.fn();
        
        render(
            <ErrorDisplay
                message="Test error"
                onRestart={mockOnRestart}
            />
        );
        
        const restartButton = screen.getByText('Start New Task');
        fireEvent.click(restartButton);
        
        expect(mockOnRestart).toHaveBeenCalledTimes(1);
    });
    
    it('displays custom title when provided', () => {
        const customTitle = 'Custom Error Title';
        
        render(
            <ErrorDisplay
                title={customTitle}
                message="Test error"
                onRestart={vi.fn()}
            />
        );
        
        expect(screen.getByText(customTitle)).toBeInTheDocument();
    });
    
    it('disables restart button when loading', () => {
        render(
            <ErrorDisplay
                message="Test error"
                onRestart={vi.fn()}
                isLoading={true}
            />
        );
        
        const restartButton = screen.getByText('Start New Task');
        expect(restartButton).toBeDisabled();
    });
});