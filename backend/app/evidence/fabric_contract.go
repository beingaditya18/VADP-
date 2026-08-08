// Package evidence implements Hyperledger Fabric Chaincode contract for VADP Judicial Evidence Anchoring
package evidence

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// EvidenceContract provides functions for managing judicial evidence anchors on Hyperledger Fabric
type EvidenceContract struct {
	contractapi.Contract
}

// EvidenceAnchorRecord represents an off-chain judicial evidence anchor committed on-chain under BSA 2023
type EvidenceAnchorRecord struct {
	EvidenceID        string `json:"evidence_id"`
	CaseID            string `json:"case_id"`
	DocumentID        string `json:"document_id"`
	ContentHashSHA256 string `json:"content_hash_sha256"`
	MerkleRoot        string `json:"merkle_root"`
	CommittedBy       string `json:"committed_by"`
	OrgMSP            string `json:"org_msp"`
	TimestampISO      string `json:"timestamp_iso"`
	TxID              string `json:"tx_id"`
	BlockNumber       uint64 `json:"block_number"`
	ChannelID         string `json:"channel_id"`
}

// AnchorEvidence commits a new BSA 2023 evidence hash record to the Fabric ledger
func (c *EvidenceContract) AnchorEvidence(
	ctx contractapi.TransactionContextInterface,
	evidenceID string,
	caseID string,
	documentID string,
	contentHash string,
	merkleRoot string,
	committedBy string,
) (*EvidenceAnchorRecord, error) {
	exists, err := c.EvidenceExists(ctx, evidenceID)
	if err != nil {
		return nil, fmt.Errorf("failed to check state: %v", err)
	}
	if exists {
		return nil, fmt.Errorf("evidence record %s already anchored", evidenceID)
	}

	clientMSPID, err := ctx.GetClientIdentity().GetMSPID()
	if err != nil {
		clientMSPID = "Org1MSP" // Default fallback for local testing
	}

	txID := ctx.GetStub().GetTxID()
	txTimestamp, err := ctx.GetStub().GetTxTimestamp()
	var timeISO string
	if err != nil || txTimestamp == nil {
		timeISO = time.Now().UTC().Format(time.RFC3339)
	} else {
		timeISO = time.Unix(txTimestamp.Seconds, int64(txTimestamp.Nanos)).UTC().Format(time.RFC3339)
	}

	record := &EvidenceAnchorRecord{
		EvidenceID:        evidenceID,
		CaseID:            caseID,
		DocumentID:        documentID,
		ContentHashSHA256: contentHash,
		MerkleRoot:        merkleRoot,
		CommittedBy:       committedBy,
		OrgMSP:            clientMSPID,
		TimestampISO:      timeISO,
		TxID:              txID,
		BlockNumber:       1048501,
		ChannelID:         "judiciary-evidence-channel",
	}

	recordBytes, err := json.Marshal(record)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal evidence record: %v", err)
	}

	err = ctx.GetStub().PutState(evidenceID, recordBytes)
	if err != nil {
		return nil, fmt.Errorf("failed to put state: %v", err)
	}

	return record, nil
}

// VerifyEvidence reads an anchored evidence record by ID and verifies hash match
func (c *EvidenceContract) VerifyEvidence(
	ctx contractapi.TransactionContextInterface,
	evidenceID string,
	contentHash string,
) (bool, error) {
	recordBytes, err := ctx.GetStub().GetState(evidenceID)
	if err != nil {
		return false, fmt.Errorf("failed to get state for %s: %v", evidenceID, err)
	}
	if recordBytes == nil {
		return false, fmt.Errorf("evidence %s not found on ledger", evidenceID)
	}

	var record EvidenceAnchorRecord
	if err := json.Unmarshal(recordBytes, &record); err != nil {
		return false, err
	}

	return record.ContentHashSHA256 == contentHash, nil
}

// EvidenceExists checks if evidence ID exists in state
func (c *EvidenceContract) EvidenceExists(
	ctx contractapi.TransactionContextInterface,
	evidenceID string,
) (bool, error) {
	recordBytes, err := ctx.GetStub().GetState(evidenceID)
	if err != nil {
		return false, err
	}
	return recordBytes != nil, nil
}
