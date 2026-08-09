const snarkjs = require('snarkjs');
const fs = require('fs');

async function benchmark() {
    const input = JSON.parse(fs.readFileSync('input_test.json'));
    const vkey = JSON.parse(fs.readFileSync('verification_key.json'));
    const proveTimes = [];
    const verifyTimes = [];
    const N = 5;

    console.log("=== In-Memory Groth16 N=5 Benchmark ===");

    for (let i = 0; i < N; i++) {
        const t0 = performance.now();
        const { proof, publicSignals } = await snarkjs.groth16.fullProve(
            input,
            'leaf_inclusion_js/leaf_inclusion.wasm',
            'leaf_inclusion_final.zkey'
        );
        const t1 = performance.now();
        proveTimes.push(t1 - t0);

        const t2 = performance.now();
        const res = await snarkjs.groth16.verify(vkey, publicSignals, proof);
        const t3 = performance.now();
        verifyTimes.push(t3 - t2);

        console.log(`  Trial ${i+1}/${N}: Prove = ${(t1-t0).toFixed(2)} ms, Verify = ${(t3-t2).toFixed(2)} ms (Valid: ${res})`);
    }

    const mean = arr => arr.reduce((a, b) => a + b, 0) / arr.length;
    const std = (arr, m) => Math.sqrt(arr.reduce((a, b) => a + Math.pow(b - m, 2), 0) / (arr.length - 1));

    const pMean = mean(proveTimes);
    const pStd = std(proveTimes, pMean);
    const vMean = mean(verifyTimes);
    const vStd = std(verifyTimes, vMean);

    console.log("\n==========================================");
    console.log(`Prove Latency:  ${pMean.toFixed(2)} ± ${pStd.toFixed(2)} ms`);
    console.log(`Verify Latency: ${vMean.toFixed(2)} ± ${vStd.toFixed(2)} ms`);
    console.log("==========================================");
}

benchmark().catch(err => {
    console.error(err);
    process.exit(1);
});
