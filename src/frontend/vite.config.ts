import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],

    // Define path aliases (similar to Create React App)
    resolve: {
        alias: {
            '@': resolve(__dirname, 'src'),
        },
    },



    // Server configuration
    server: {
        port: 3001,
        open: true,
        host: true
    },

    // Build configuration
    build: {
        outDir: 'build',
        sourcemap: true,
        // Optimize dependencies
        rollupOptions: {
            output: {
                manualChunks: {
                    vendor: ['react', 'react-dom'],
                    fluentui: ['@fluentui/react-components', '@fluentui/react-icons'],
                    router: ['react-router-dom'],
                }
            }
        }
    },

    // Handle CSS and static assets
    css: {
        modules: {
            localsConvention: 'camelCase'
        }
    },

    // Environment variables configuration
    envPrefix: 'REACT_APP_',

    // Define global constants - only expose specific env vars needed by frontend
    define: {
        'process.env.REACT_APP_API_URL': JSON.stringify(process.env.REACT_APP_API_URL || 'http://localhost:8000'),
        'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
    },

    // Optimization
    optimizeDeps: {
        include: [
            'react',
            'react-dom',
            '@fluentui/react-components',
            '@fluentui/react-icons',
            'react-router-dom',
            'axios'
        ]
    }
})