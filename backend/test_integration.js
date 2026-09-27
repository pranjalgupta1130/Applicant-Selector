const http = require('http');

const request = (method, path, body = null) => {
  return new Promise((resolve, reject) => {
    const dataString = body ? JSON.stringify(body) : '';
    const req = http.request(
      {
        hostname: 'localhost',
        port: 5000,
        path,
        method,
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(dataString)
        }
      },
      (res) => {
        let responseData = '';
        res.on('data', (chunk) => (responseData += chunk));
        res.on('end', () => {
          try {
            const parsed = responseData ? JSON.parse(responseData) : {};
            resolve({ statusCode: res.statusCode, body: parsed });
          } catch (e) {
            resolve({ statusCode: res.statusCode, raw: responseData });
          }
        });
      }
    );
    req.on('error', reject);
    if (body) req.write(dataString);
    req.end();
  });
};

const runTests = async () => {
  console.log('--- STARTING COMBINED TASKS 2-5 INTEGRATION TEST ---');

  // Step 1: Health
  const healthRes = await request('GET', '/api/health');
  console.log('1. Health Check:', healthRes.statusCode, healthRes.body.status === 'ok' ? 'PASS' : 'FAIL');

  // Step 2: Roles List
  const rolesRes = await request('GET', '/api/roles');
  console.log('2. Roles List:', rolesRes.statusCode, rolesRes.body.count > 0 ? 'PASS' : 'FAIL');
  const role = rolesRes.body.data[0];
  const roleId = role._id;
  console.log('   └─ Seeded Role ID:', roleId, '| Title:', role.title, '| Competencies:', role.competencies.length);

  // Step 3: Single Role Fetch
  const roleSingleRes = await request('GET', `/api/roles/${roleId}`);
  console.log('3. Single Role Fetch:', roleSingleRes.statusCode, roleSingleRes.body.data.title === role.title ? 'PASS' : 'FAIL');

  // Step 4: Candidate Creation
  const candidateBody = {
    name: 'Demo Synthetic Candidate',
    email: 'synthetic.candidate@example.com',
    experience: '2 years of backend engineering experience',
    education: 'B.E. Computer Engineering',
    extractedSkills: ['Node.js', 'Express', 'JavaScript', 'REST APIs', 'MongoDB']
  };
  const candRes = await request('POST', '/api/candidates', candidateBody);
  const candidateId = candRes.body.data._id;
  console.log('4. Candidate Creation:', candRes.statusCode, candidateId ? 'PASS' : 'FAIL');
  console.log('   └─ Created Candidate ID:', candidateId);

  // Step 5: Resume Reference Update
  const resumeBody = { resumeUrl: 'https://example.com/synthetic-resume.pdf' };
  const resumeRes = await request('POST', `/api/candidates/${candidateId}/resume`, resumeBody);
  console.log('5. Resume Reference Update:', resumeRes.statusCode, resumeRes.body.data.resumeUrl === resumeBody.resumeUrl ? 'PASS' : 'FAIL');

  // Step 6: Candidate Fetch
  const candFetchRes = await request('GET', `/api/candidates/${candidateId}`);
  console.log('6. Candidate Fetch:', candFetchRes.statusCode, candFetchRes.body.data.resumeUrl === resumeBody.resumeUrl ? 'PASS' : 'FAIL');

  // Step 7: Create Interview Session
  const interviewBody = { candidateId, roleId };
  const interviewRes = await request('POST', '/api/interviews', interviewBody);
  if (!interviewRes.body.data) {
    console.error('7. Create Interview Session FAIL Response Body:', JSON.stringify(interviewRes.body));
    return;
  }
  const interviewId = interviewRes.body.data._id;
  console.log('7. Create Interview Session:', interviewRes.statusCode, interviewRes.body.data.status === 'created' ? 'PASS' : 'FAIL');
  console.log('   └─ Created Interview ID:', interviewId, '| Status:', interviewRes.body.data.status, '| Stage:', interviewRes.body.data.currentStage);

  // Step 8: Get Interview Session
  const interviewFetchRes = await request('GET', `/api/interviews/${interviewId}`);
  console.log('8. Get Interview Session:', interviewFetchRes.statusCode, interviewFetchRes.body.data.status === 'created' ? 'PASS' : 'FAIL');

  // Step 9: Start Interview Session
  const startRes1 = await request('POST', `/api/interviews/${interviewId}/start`);
  const startedAt1 = startRes1.body.data.startedAt;
  console.log('9. Start Interview Session:', startRes1.statusCode, startRes1.body.data.status === 'in_progress' ? 'PASS' : 'FAIL');
  console.log('   └─ Status:', startRes1.body.data.status, '| Stage:', startRes1.body.data.currentStage, '| StartedAt:', startedAt1);

  // Step 10: Idempotent Repeat Start
  const startRes2 = await request('POST', `/api/interviews/${interviewId}/start`);
  const startedAt2 = startRes2.body.data.startedAt;
  const isIdempotent = startRes2.body.data.status === 'in_progress' && startedAt1 === startedAt2;
  console.log('10. Idempotency Check:', startRes2.statusCode, isIdempotent ? 'PASS' : 'FAIL');

  // Step 11: Persistence Verification
  const persistRes = await request('GET', `/api/interviews/${interviewId}`);
  console.log('11. Persistence Verification:', persistRes.statusCode, persistRes.body.data.status === 'in_progress' ? 'PASS' : 'FAIL');

  // Step 12: Negative Cases
  const invalidRoleRes = await request('GET', '/api/roles/invalid-id-format');
  const nonExistCandidateRes = await request('POST', '/api/interviews', { candidateId: '000000000000000000000000', roleId });
  const nonExistStartRes = await request('POST', '/api/interviews/000000000000000000000000/start');

  const negPass = invalidRoleRes.statusCode === 400 && nonExistCandidateRes.statusCode === 404 && nonExistStartRes.statusCode === 404;
  console.log('12. Negative Cases Validation:', negPass ? 'PASS' : 'FAIL');
  console.log('   └─ Invalid ID Code:', invalidRoleRes.statusCode, '| Nonexistent Candidate Code:', nonExistCandidateRes.statusCode, '| Nonexistent Start Code:', nonExistStartRes.statusCode);

  console.log('--- INTEGRATION TEST COMPLETE ---');
};

runTests();
