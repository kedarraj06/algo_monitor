def engineer_features(extracted: dict) -> dict:
    contract_length = extracted["contract_length"]
    num_txn = extracted["num_txn"]
    num_and = extracted["num_and"]
    num_or = extracted["num_or"]
    
    txn_per_length = num_txn / (contract_length + 1)
    logic_density = (num_and + num_or) / (contract_length + 1)
    security_checks = extracted["has_rekey_check"] + extracted["has_close_check"] + extracted["has_receiver_check"]
    txn_logic_ratio = num_txn / (num_and + num_or + 1)
    
    extracted.update({
        "txn_per_length": txn_per_length,
        "logic_density": logic_density,
        "security_checks": security_checks,
        "txn_logic_ratio": txn_logic_ratio
    })
    
    return extracted
