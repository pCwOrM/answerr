// Evaluates tests/policy_vectors.json with the JS kernel and prints the results
// as JSON, so tests/test_policy_kernel.py can compare them with the Python kernel.
const fs = require('fs');
const path = require('path');
const K = require(path.join(__dirname, '..', 'js', 'policy-kernel.js'));

const root = path.join(__dirname, '..');
const vectors = JSON.parse(fs.readFileSync(path.join(root, 'tests', 'policy_vectors.json'), 'utf8'));
const gates = JSON.parse(fs.readFileSync(path.join(root, 'policies', 'builtin_gates.json'), 'utf8'));

const out = vectors.map(v => {
  const policy = typeof v.gate === 'string' ? gates[v.gate] : (v.gate || null);
  const r = K.evaluate(v.state, policy, Boolean(v.strict));
  return { name: v.name, result: r, answer: K.answerQuestion(r, v.question) };
});
const seals = {};
Object.keys(gates).sort().forEach(g => { seals[g] = K.policySeal(gates[g]); });
process.stdout.write(JSON.stringify({ results: out, seals }));
