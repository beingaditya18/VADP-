pragma circom 2.0.0;

/*
 * Nyaya-ZTA Groth16 Leaf Inclusion Circuit
 * ==========================================
 * Proves that a document leaf is included in a Merkle tree
 * WITHOUT revealing the document contents.
 *
 * Public signals:  leaf (the RFC6962 leaf hash), root (expected Merkle root)
 * Private signals: pathElements[DEPTH], pathIndices[DEPTH]
 *
 * Compiled with: circom leaf_inclusion.circom --r1cs --wasm --sym
 * Proving system: Groth16 (snarkjs groth16 setup / prove / verify)
 *
 * Usage (snarkjs CLI):
 *   snarkjs groth16 setup leaf_inclusion.r1cs pot12_final.ptau leaf_inclusion.zkey
 *   snarkjs groth16 prove leaf_inclusion.zkey witness.wtns proof.json public.json
 *   snarkjs groth16 verify verification_key.json public.json proof.json
 */

include "node_modules/circomlib/circuits/poseidon.circom";
include "node_modules/circomlib/circuits/mux1.circom";

/*
 * MerklePathHasher: computes one level of the Merkle path.
 * Uses Poseidon hash (ZK-friendly, ~3x fewer constraints than SHA-256).
 */
template MerklePathHasher() {
    signal input left;
    signal input right;
    signal output out;

    component h = Poseidon(2);
    h.inputs[0] <== left;
    h.inputs[1] <== right;
    out <== h.out;
}

/*
 * LeafInclusion(DEPTH): proves leaf ∈ Merkle tree with given root.
 *
 * DEPTH = 10 supports up to 2^10 = 1,024 leaves (sufficient for 60k-vector vault
 * with periodic batch anchoring every 1,024 documents).
 */
template LeafInclusion(DEPTH) {
    // Public inputs
    signal input leaf;              // RFC6962 leaf hash (Poseidon representation)
    signal input root;              // Expected Merkle root

    // Private inputs (witness)
    signal input pathElements[DEPTH];   // Sibling hashes along the path
    signal input pathIndices[DEPTH];    // 0 = current node is left, 1 = right

    // Internal signals
    signal current[DEPTH + 1];
    current[0] <== leaf;

    component hashers[DEPTH];
    component muxLeft[DEPTH];
    component muxRight[DEPTH];

    for (var i = 0; i < DEPTH; i++) {
        // Select left/right based on pathIndices[i]
        muxLeft[i]  = Mux1();
        muxRight[i] = Mux1();

        muxLeft[i].c[0]  <== current[i];
        muxLeft[i].c[1]  <== pathElements[i];
        muxLeft[i].s     <== pathIndices[i];

        muxRight[i].c[0] <== pathElements[i];
        muxRight[i].c[1] <== current[i];
        muxRight[i].s    <== pathIndices[i];

        hashers[i] = MerklePathHasher();
        hashers[i].left  <== muxLeft[i].out;
        hashers[i].right <== muxRight[i].out;

        current[i + 1] <== hashers[i].out;
    }

    // Enforce that computed root matches the public root signal
    root === current[DEPTH];
}

component main { public [leaf, root] } = LeafInclusion(10);
