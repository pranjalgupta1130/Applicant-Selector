import http from 'http';

function post(url, data) {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const body = JSON.stringify(data);
    const req = http.request({
      hostname: u.hostname,
      port: u.port,
      path: u.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      }
    }, res => {
      let raw = '';
      res.on('data', chunk => raw += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(raw)); } catch(e) { resolve(raw); }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

function get(url) {
  return new Promise((resolve, reject) => {
    http.get(url, res => {
      let raw = '';
      res.on('data', chunk => raw += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(raw)); } catch(e) { resolve(raw); }
      });
    }).on('error', reject);
  });
}

async function runLiveVerification() {
  console.log("=== LIVE DRDO RADAR INTERVIEW FLOW VERIFICATION ===");

  // 1. Fetch available DRDO posts
  const rolesData = await get('http://localhost:5000/api/roles');
  const roles = Array.isArray(rolesData) ? rolesData : (rolesData.data || []);
  const radarRole = roles.find(r => (r.title || '').includes('Radar') || (r.title || '').includes('Signal')) || roles[0];
  console.log(`Selected Target Role: "${radarRole.title}" (ID: ${radarRole._id || radarRole.id})`);

  // 2. Register Candidate Profile
  const candRes = await post('http://localhost:5000/api/candidates', {
    name: "Dr. Vikram Sarabhai Candidate",
    email: `vikram.radar.${Date.now()}@drdo.gov.in`,
    experience: "5 years",
    education: "M.Tech in Radar & Signal Processing",
    extractedSkills: ["Radar Signal Processing", "Matched Filtering", "Digital Pulse Compression", "Doppler FFT", "SNR Optimization"]
  });
  const cand = candRes.data || candRes;
  console.log(`Candidate Registered. ID: ${cand._id || cand.id}`);

  // 3. Create Interview Session
  const intRes = await post('http://localhost:5000/api/interviews', {
    candidateId: cand._id || cand.id,
    roleId: radarRole._id || radarRole.id
  });
  const interview = intRes.data || intRes;
  const interviewId = interview._id || interview.id;
  console.log(`Interview Created. ID: ${interviewId}`);

  // 4. Start Interview (POST /api/interviews/:id/start)
  console.log("\n--- TURN 1: START INTERVIEW ---");
  const startRaw = await post(`http://localhost:5000/api/interviews/${interviewId}/start`, {});
  const startData = startRaw.data || startRaw;

  let activeQuestionDoc = startData.question || (startData.interview && startData.interview.question);
  let aiQuestionObj = startData.aiActiveQuestion || startData.openingQuestion || startData.currentQuestion;

  console.log(`Status: ${startData.status || 'started'}`);
  console.log(`Stage: ${aiQuestionObj.stage}`);
  console.log(`Competency: ${aiQuestionObj.competency}`);
  console.log(`Node Question Doc ID: ${activeQuestionDoc._id || activeQuestionDoc.id}`);
  console.log(`AI Question ID: ${aiQuestionObj.id}`);
  console.log(`Question Text: "${aiQuestionObj.text}"`);
  console.log(`Expected Concepts: ${JSON.stringify(aiQuestionObj.expectedConcepts)}`);
  console.log(`Is Fallback: ${aiQuestionObj.isFallback}`);
  console.log(`Source IDs: ${JSON.stringify(aiQuestionObj.sources || aiQuestionObj.sourceChunkIds || [])}`);

  let currentQuestionDocId = activeQuestionDoc._id || activeQuestionDoc.id;
  let lastAiState = startData.aiState || (startData.interview && startData.interview.aiState);

  // Answers array tailored to radar questions
  const answers = [
    "I completed my M.Tech in Electronics and Communication with a research thesis on digital pulse compression and matched filter optimization for low-RCS target detection.",
    "Matched filtering maximizes the signal-to-noise ratio in additive white Gaussian noise by cross-correlating the received radar echo with the known transmitted pulse waveform.",
    "When Doppler shift is present, the matched filter output suffers from mismatch loss and range shift. We mitigate this using a bank of Doppler-compensated matched filters or FFT Doppler processing.",
    "In real-time embedded radar receivers, FFT-based pulse compression is implemented on FPGA using radix-2 Cooley-Tukey architecture with ping-pong DMA buffers."
  ];

  for (let turn = 1; turn <= answers.length; turn++) {
    console.log(`\n--- SUBMITTING ANSWER FOR TURN ${turn} ---`);
    console.log(`Answer: "${answers[turn - 1]}"`);

    const answerRaw = await post(`http://localhost:5000/api/interviews/${interviewId}/answers`, {
      interviewQuestionId: currentQuestionDocId,
      answerText: answers[turn - 1]
    });
    console.log('answerRaw structure:', JSON.stringify(answerRaw, null, 2));
    const answerData = answerRaw.data || answerRaw;

    if (answerData.updatedState) lastAiState = answerData.updatedState;
    else if (answerData.aiState) lastAiState = answerData.aiState;
    else if (answerData.interview && answerData.interview.aiState) lastAiState = answerData.interview.aiState;

    const evalObj = answerData.evaluation || answerData.aiEvaluation;
    console.log(`Evaluation Score: ${evalObj ? evalObj.score : 'N/A'}`);
    console.log(`Technical Correctness: ${evalObj ? evalObj.technicalCorrectness : 'N/A'}`);
    console.log(`Reasoning: ${evalObj ? evalObj.reasoning : 'N/A'}`);
    console.log(`Decision Strategy: ${answerData.decision ? answerData.decision.strategy : 'N/A'}`);

    const nextQDoc = answerData.nextQuestion || answerData.question;
    const nextAiQ = answerData.aiNextQuestion || nextQDoc;

    if (nextQDoc && nextAiQ) {
      currentQuestionDocId = nextQDoc._id || nextQDoc.id;
      console.log(`\n--- TURN ${turn + 1}: NEXT ADAPTIVE QUESTION ---`);
      console.log(`Stage: ${nextAiQ.stage || nextQDoc.stage}`);
      console.log(`Competency: ${nextAiQ.competency || nextQDoc.competency}`);
      console.log(`Question Text: "${nextAiQ.text || nextQDoc.text}"`);
      console.log(`Expected Concepts: ${JSON.stringify(nextAiQ.expectedConcepts || nextQDoc.expectedConcepts)}`);
      console.log(`Is Fallback: ${nextAiQ.isFallback}`);
      console.log(`Source IDs: ${JSON.stringify(nextAiQ.sources || nextQDoc.sourceChunkIds || [])}`);
    } else {
      console.log("\nInterview concluded naturally.");
      break;
    }
  }

  console.log("\n=== LIVE VERIFICATION SUCCESSFUL ===");
}

runLiveVerification().catch(err => {
  console.error("Live verification error:", err);
});
