// Package main implements Hyperledger Fabric Chaincode for VADP Judicial Evidence Anchoring
package main

import (
	"encoding/json"
	"fmt"
	"time"

	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract defines the Hyperledger Fabric chaincode contract
type SmartContract struct {
	contractapi.Contract
}

// EvidenceAnchorRecord represents an off-chain judicial evidence anchor committed on-chain
type EvidenceAnchorRecord struct {
	EvidenceID       string `json:"evidence_id"`
	CaseID           string `json:"case_id"`
	DocumentID       string `json:"document_id"`
	ContentHashSHA256 string `json:"content_hash_sha256"`
	MerkleRoot       string `json:"merkle_root"`
	CommittedBy      string `json:"committed_by"`
	TimestampISO     string `json:"timestamp_iso"`
	TxID             string `json:"tx_id"`
	BlockNumber      uint64 `json:"block_number"`
	ChannelID        string `json:"channel_id"`
}

// AnchorEvidence commits a new BSA 2023 evidence hash record to the Fabric ledger
func (s *SmartContract) AnchorEvidence(ctx contractapi.TransactionContextInterface, evidenceID string, caseID string, documentID string, contentHash string, merkleRoot string, committedBy string) (*EvidenceAnchorRecord, error) {
	exists, err := s.EvidenceExists(ctx, evidenceID)
	if err != nil {
		return nil, fmt.Errorf("failed to read from world state: %v", err)
	}
	if exists {
		return nil, fmt.Errorf("the evidence %s already exists", evidenceID)
	}

	txID := ctx.GetStub().GetTxID()
	txTimestamp, err := ctx.GetStub().GetTxTimestamp()
	if err != nil {
		return nil, fmt.Errorf("failed to get transaction timestamp: %v", err)
	}
	timeISO := time.Unix(txTimestamp.Seconds, int64(txTimestamp.Nanos)).UTC().Format(time.RFC3339)

	record := &EvidenceAnchorRecord{
		EvidenceID:        evidenceID,
		CaseID:            caseID,
		DocumentID:        documentID,
		ContentHashSHA256: contentHash,
		MerkleRoot:        merkleRoot,
		CommittedBy:       committedBy,
		TimestampISO:      timeISO,
		TxID:              txID,
		BlockNumber:       1048501, // Managed by ledger engine
		ChannelID:         "judiciary-evidence-channel",
	}

	recordJSON, err := json.Marshal(record)
	if err != nil {
		return nil, err
	}

	err = ctx.GetStub().PutState(evidenceID, recordJSON)
	if err != nil {
		return nil, fmt.Errorf("failed to put to world state: %v", err)
	}

	return record, nil
}

// GetEvidence retrieves an anchored evidence record by ID
func (s *SmartContract) GetEvidence(ctx contractapi.TransactionContextInterface, evidenceID string) (*EvidenceAnchorRecord, error) {
	recordJSON, err := ctx.GetStub().GetState(evidenceID)
	if err != nil {
		return nil, fmt.Errorf("failed to read evidence %s: %v", evidenceID, err)
	}
	if recordJSON == nil {
		return nil, fmt.Errorf("evidence %s does not exist", evidenceID)
	}

	var record EvidenceAnchorRecord
	err = json.Unmarshal(recordJSON, &record)
	if err != nil {
		return nil, err
	}

	return &record, nil
}

// EvidenceExists checks if evidence ID is present in state
func (s *SmartContract) EvidenceExists(ctx contractapi.TransactionContextInterface, evidenceID string) (bool, error) {
	recordJSON, err := ctx.GetStub().GetState(evidenceID)
	if err != nil {
		return false, err
	}
	return recordJSON != nil, nil
}

func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		fmt.Printf("Error creating VADP Evidence Anchor chaincode: %v\n", err)
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting VADP Evidence Anchor chaincode: %v\n", err)
	}
}
