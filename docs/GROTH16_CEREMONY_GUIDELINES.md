# VADP Multi-Party Computation (MPC) Ceremony Guidelines for Groth16 Trusted Setup

## Executive Summary

To deploy Groth16 zero-knowledge SNARK circuits for privacy-preserving judicial evidence verification without relying on a single trusted entity, VADP enforces a decentralized Multi-Party Computation (MPC) trusted setup ceremony across physically separate, independently-controlled participant infrastructure operated by distinct organizations (e.g., Supreme Court e-Committee, Bar Association, National Forensic Sciences University, Ministry of Law & Justice).

Under the 1-out-of-$N$ trust model, if **at least one participant** honestly destroys their secret toxic waste randomness, the resulting proving key ($\text{zkey}$) and verification key ($\text{vkey}$) remain cryptographically secure against false proof forgery.

---

## 1. Ceremony Architecture & Multi-Org Infrastructure

The trusted setup consists of two sequential phases executed across distributed infrastructure:

```
+---------------------------------------------------------------------------------+
| PHASE 1: Universal Powers-of-Tau Ceremony (BN128 / BN254 Curve)                 |
| Participant Nodes: Org1 (Supreme Court), Org2 (High Court), Org3 (Forensic Lab) |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| PHASE 2: Circuit-Specific Compilation & Contribution                            |
| (LeafInclusion_d10, LeafInclusion_d15, LeafInclusion_d20)                        |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| PUBLIC RANDOM BEACON & FINAL VERIFICATION KEY EXTRACTION                         |
| (Hash Anchor: NIST Randomness Beacon / Bitcoin Block Header)                    |
+---------------------------------------------------------------------------------+
```

---

## 2. Phase 1: Universal Powers-of-Tau Setup

1. **Parameters**: Scale $2^{16} = 65,536$ constraints (supporting Merkle tree inclusion circuits up to depth 20).
2. **Curve**: BN128 (alt_bn128) pairing-friendly elliptic curve.
3. **Execution Protocol**:
   ```bash
   # Initialize Phase 1 Powers of Tau
   npx snarkjs powersoftau new bn128 16 pot16_0000.ptau -v

   # Participant 1 Contribution (Supreme Court e-Committee)
   npx snarkjs powersoftau contribute pot16_0000.ptau pot16_0001.ptau --name="Supreme Court e-Committee Node 1" -v -e="RandomEntropyString1..."

   # Participant 2 Contribution (Bar Association Node)
   npx snarkjs powersoftau contribute pot16_0001.ptau pot16_0002.ptau --name="Bar Association Node 2" -v -e="RandomEntropyString2..."

   # Participant 3 Contribution (National Forensic Sciences University)
   npx snarkjs powersoftau contribute pot16_0002.ptau pot16_0003.ptau --name="NFSU Forensic Node 3" -v -e="RandomEntropyString3..."

   # Prepare Phase 2
   npx snarkjs powersoftau prepare phase2 pot16_0003.ptau pot16_final.ptau -v
   ```

---

## 3. Phase 2: Circuit-Specific Contributions

Each VADP circuit (`LeafInclusion_d10`, `LeafInclusion_d15`, `LeafInclusion_d20`) receives independent Phase 2 contributions from judicial stakeholders:

```bash
# 1. Compile Circom Circuit
circom LeafInclusion_d10.circom --r1cs --wasm --sym

# 2. Setup Groth16 Proving Key
npx snarkjs groth16 setup LeafInclusion_d10.r1cs pot16_final.ptau LeafInclusion_d10_0000.zkey

# 3. Judicial Stakeholder Contributions
npx snarkjs zkey contribute LeafInclusion_d10_0000.zkey LeafInclusion_d10_0001.zkey --name="High Court Node" -v -e="EntropyA..."
npx snarkjs zkey contribute LeafInclusion_d10_0001.zkey LeafInclusion_d10_0002.zkey --name="Supreme Court e-Committee Node" -v -e="EntropyB..."

# 4. Apply Public Random Beacon (e.g., NIST Beacon / Bitcoin block hash)
npx snarkjs zkey beacon LeafInclusion_d10_0002.zkey LeafInclusion_d10_final.zkey 0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f 10 -n="Final Judicial Beacon"

# 5. Export Verification Key
npx snarkjs zkey export verificationkey LeafInclusion_d10_final.zkey verification_key.json
```

---

## 4. Toxic Waste Destruction & Independent Verification

* **Memory Air-Gapping**: Participants run contributions inside ephemeral, air-gapped RAM-disk instances (Tails OS or Docker `--tmpfs`).
* **Entropy Sources**: CSPRNG (`/dev/urandom`), hardware timing jitter, and block hash beacons.
* **Public Audit Log**: Every `.zkey` contribution hash is logged to the VADP Merkle audit ledger, permitting independent verification:
  ```bash
  npx snarkjs zkey verify LeafInclusion_d10.r1cs pot16_final.ptau LeafInclusion_d10_final.zkey
  ```
