const { readCollection, writeCollection, generateId } = require('../storage/jsonStore');

const roles = [
  ['Scientist B — Aerodynamics', 'Compressible flow, computational fluid dynamics, flight loads, and vehicle stability.', ['computational_fluid_dynamics', 'aerospace_aerodynamics', 'aerospace_fundamentals'], 'drdo_scientist_aerospace', 'aerospace_aerodynamics'],
  ['Scientist C — Radar Signal Processing', 'Radar detection, digital signal processing, clutter modelling, and adaptive beamforming.', ['embedded_realtime_systems', 'digital_signal_processing', 'radar_rf_systems'], 'drdo_scientist_radar', 'electronics_radar'],
  ['Scientist B — Composite Materials', 'Fibre-matrix mechanics, failure criteria, and thermal ageing.', ['composite_materials', 'materials_science'], 'drdo_scientist_materials', 'aerospace_aerodynamics'],
  ['Scientist C — Guidance & Control', 'State estimation, nonlinear control, and seeker integration.', ['control_systems', 'state_estimation'], 'drdo_scientist_guidance', 'electronics_radar'],
  ['Scientist B — Cybersecurity', 'Network security, threat analysis, secure systems, and incident response.', ['cybersecurity', 'network_security', 'incident_response'], 'drdo_scientist_cyber', 'cyber_computing']
];

async function seedDemo() {
  const current = await readCollection('roles');
  for (const [title, description, competencies, aiRoleId, domain] of roles) {
    const existing = current.find((r) => r.title === title);
    const role = existing || { _id: generateId(), createdAt: new Date().toISOString() };
    Object.assign(role, { title, description, competencies: competencies.map((name) => ({ name })), aiRoleId, domain, difficulty: 3, isActive: true, updatedAt: new Date().toISOString() });
    if (!existing) current.push(role);
  }
  await writeCollection('roles', current);
  const demoCandidates = [
    ['Dr. Vikram Sharma', 'vikram.sharma@example.test', ['Radar Signal Processing', 'DSP', 'Detection Theory']],
    ['Test Candidate — Aerodynamics', 'aero.candidate@example.test', ['Computational Fluid Dynamics', 'Aerodynamics', 'Turbulence Modelling']],
    ['Test Candidate — Cybersecurity', 'security.candidate@example.test', ['Cybersecurity', 'Network Security', 'Incident Response']]
  ];
  const candidates = await readCollection('candidates');
  for (const [name, email, extractedSkills] of demoCandidates) {
    if (!candidates.some((c) => c.email?.toLowerCase() === email)) candidates.push({ _id: generateId(), name, email, extractedSkills, experience: '5', education: 'Engineering', resumeUrl: '', createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() });
  }
  await writeCollection('candidates', candidates);
  console.log(`Seeded ${roles.length} DRDO roles and ${demoCandidates.length} demo candidate profiles (repeat-safe).`);
}

if (require.main === module) seedDemo().catch((error) => { console.error(error); process.exitCode = 1; });
module.exports = seedDemo;
