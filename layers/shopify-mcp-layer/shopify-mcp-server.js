#!/usr/bin/env node

/**
 * Shopify MCP Server for Lambda Layer
 * Provides Shopify Storefront API integration via MCP protocol
 */

const { Server } = require('@shopify/mcp-server-storefront');

// Environment configuration
const config = {
  storeUrl: process.env.SHOPIFY_STORE_URL,
  accessToken: process.env.SHOPIFY_ACCESS_TOKEN,
  storefrontAccessToken: process.env.SHOPIFY_STOREFRONT_ACCESS_TOKEN,
  
  // Server configuration
  name: 'shopify-storefront',
  version: '1.0.0',
  
  // Timeout configuration
  timeout: 30000,
  
  // Logging configuration
  logLevel: process.env.LOG_LEVEL || 'info'
};

// Validate required environment variables
const requiredEnvVars = [
  'SHOPIFY_STORE_URL',
  'SHOPIFY_ACCESS_TOKEN', 
  'SHOPIFY_STOREFRONT_ACCESS_TOKEN'
];

for (const envVar of requiredEnvVars) {
  if (!process.env[envVar]) {
    console.error(`Missing required environment variable: ${envVar}`);
    process.exit(1);
  }
}

// Initialize and start the MCP server
async function startServer() {
  try {
    console.log('Starting Shopify MCP Server...');
    console.log(`Store URL: ${config.storeUrl}`);
    
    const server = new Server(config);
    
    // Handle graceful shutdown
    process.on('SIGINT', async () => {
      console.log('Received SIGINT, shutting down gracefully...');
      await server.close();
      process.exit(0);
    });
    
    process.on('SIGTERM', async () => {
      console.log('Received SIGTERM, shutting down gracefully...');
      await server.close();
      process.exit(0);
    });
    
    // Start the server
    await server.start();
    console.log('Shopify MCP Server started successfully');
    
  } catch (error) {
    console.error('Failed to start Shopify MCP Server:', error);
    process.exit(1);
  }
}

// Start the server
startServer();
