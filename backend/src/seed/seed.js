const dns = require('dns');
try {
  dns.setServers(['8.8.8.8', '1.1.1.1']);
  if (dns.setDefaultResultOrder) {
    dns.setDefaultResultOrder('ipv4first');
  }
} catch (e) {}

require('dotenv').config();
const connectDB = require('../config/db');

const demoCompetencies = [
  {
    name: 'Programming',
    category: 'technical',
    description: 'Core programming syntax, OOP principles, data structures, and code execution complexity.',
    weight: 1.0
  },
  {
    name: 'Backend',
    category: 'technical',
    description: 'RESTful API architecture, HTTP protocol, authentication/authorization, and backend middleware.',
    weight: 1.0
  },
  {
    name: 'Database',
    category: 'technical',
    description: 'SQL vs NoSQL databases, indexing strategies, transactions, normalization, and query optimization.',
    weight: 1.0
  },
  {
    name: 'System Design',
    category: 'technical',
    description: 'System scalability, distributed caching, message queues, load balancing, and high availability.',
    weight: 1.0
  },
  {
    name: 'CS Fundamentals',
    category: 'fundamentals',
    description: 'Operating systems principles, computer networking, processes/threads, and memory management.',
    weight: 1.0
  },
  {
    name: 'Problem Solving',
    category: 'technical',
    description: 'Algorithmic reasoning, trade-off evaluation, edge case handling, and systematic debugging.',
    weight: 1.0
  },
  {
    name: 'Managerial / Scenario',
    category: 'managerial',
    description: 'Production incident handling, technical debt prioritization, team collaboration, and decision-making.',
    weight: 1.0
  }
];

const seedDemoRole = async () => {
  try {
    console.log('[Seed Script] Connecting to database...');
    await connectDB();

    // Import models AFTER database connection is established
    const { Competency, Role } = require('../models');

    console.log('[Seed Script] Seeding competencies...');
    const competencyIds = [];

    for (const compData of demoCompetencies) {
      const competency = await Competency.findOneAndUpdate(
        { name: compData.name },
        compData,
        { upsert: true, new: true, setDefaultsOnInsert: true }
      );
      competencyIds.push(competency._id);
      console.log(`  └─ Competency: ${competency.name} (${competency._id})`);
    }

    console.log('[Seed Script] Seeding demo role...');
    const demoRoleData = {
      title: 'Backend / Full-Stack Software Engineer',
      description: 'Primary hackathon demo role for evaluating candidate proficiency across API design, database architecture, CS fundamentals, system design, and techno-managerial scenarios.',
      difficulty: 3,
      competencies: competencyIds,
      isActive: true
    };

    const role = await Role.findOneAndUpdate(
      { title: demoRoleData.title },
      demoRoleData,
      { upsert: true, new: true, setDefaultsOnInsert: true }
    );

    console.log(`  └─ Demo Role Created/Updated: ${role.title} (${role._id})`);
    console.log('[Seed Script] Seed process completed successfully!');
    process.exit(0);
  } catch (error) {
    console.error('[Seed Script Error] Seeding failed:', error.message);
    process.exit(1);
  }
};

// Execute seed if run directly
if (require.main === module) {
  seedDemoRole();
}

module.exports = seedDemoRole;
