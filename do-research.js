#!/usr/bin/env node
/**
 * Flight Research Script
 * Runs web searches for booking strategies
 * 
 * Note: Requires Brave Search API to be configured in OpenClaw
 * This is meant to be run by Gerald (the agent) via exec
 */

const queries = [
  {
    topic: 'Booking Window',
    query: 'best time to book flights to Greece June advance purchase window days before'
  },
  {
    topic: 'Amex Points',
    query: 'Amex Platinum transfer partners Athens Greece Virgin Atlantic Air France points value'
  },
  {
    topic: 'Route Tips',
    query: 'San Diego to Athens best layover cities connection times airline recommendations'
  },
  {
    topic: 'Seasonal Pricing',
    query: 'Greece flight prices June peak season trends 2026 summer'
  }
];

console.log('📚 Flight Research Topics:\n');
queries.forEach((q, i) => {
  console.log(`${i + 1}. ${q.topic}`);
  console.log(`   Query: "${q.query}"\n`);
});

console.log('\n💡 Run these searches via OpenClaw web_search tool');
console.log('   (Brave API now configured)\n');
