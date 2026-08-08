pragma circom 2.0.0;

/*
 * EvidenceInclusionProof Circuit
 * Verifies zero-knowledge inclusion of private evidence hash in custody chain Merkle root.
 */

template SHA256Compress() {
    signal input left[256];
    signal input right[256];
    signal output hash[256];

    // SHA-256 compression function constraints placeholder
    for (var i = 0; i < 256; i++) {
        hash[i] <== left[i] ^ right[i];
    }
}

template EvidenceMerkleInclusion(depth) {
    // Private Signals
    signal input private_evidence_hash[256];
    signal input path_elements[depth][256];
    signal input path_index[depth];

    // Public Signals
    signal input expected_merkle_root[256];

    // Intermediate Hashes
    signal hashes[depth + 1][256];

    for (var i = 0; i < 256; i++) {
        hashes[0][i] <== private_evidence_hash[i];
    }

    component selectors[depth];
    for (var d = 0; d < depth; d++) {
        selectors[d] = SHA256Compress();
        for (var i = 0; i < 256; i++) {
            selectors[d].left[i] <== hashes[d][i] + path_index[d] * (path_elements[d][i] - hashes[d][i]);
            selectors[d].right[i] <== path_elements[d][i] + path_index[d] * (hashes[d][i] - path_elements[d][i]);
        }
        for (var i = 0; i < 256; i++) {
            hashes[d + 1][i] <== selectors[d].hash[i];
        }
    }

    // Constraint: Reconstructed Root MUST EQUAL Expected Root
    for (var i = 0; i < 256; i++) {
        expected_merkle_root[i] === hashes[depth][i];
    }
}

component main {public [expected_merkle_root]} = EvidenceMerkleInclusion(4);
