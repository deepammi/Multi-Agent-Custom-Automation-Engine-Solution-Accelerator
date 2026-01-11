// vitest-dom adds custom vitest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// Setup DOM environment for React 18 createRoot
import { beforeEach, afterEach } from 'vitest';
import { cleanup } from '@testing-library/react';

beforeEach(() => {
  // Ensure we have a clean DOM for each test
  document.body.innerHTML = '';
  const div = document.createElement('div');
  div.id = 'root';
  document.body.appendChild(div);
});

afterEach(() => {
  // Clean up React Testing Library
  cleanup();
  // Clean up the DOM after each test
  document.body.innerHTML = '';
});
