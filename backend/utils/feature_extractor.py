def extract_features_from_teal(content: str) -> dict:
    lines = content.split('\n')
    
    has_rekey = 1 if "RekeyTo" in content and "ZeroAddress" in content else 0
    has_close = 1 if "CloseRemainderTo" in content and "ZeroAddress" in content else 0
    has_receiver = 1 if "Receiver" in content else 0
    
    num_txn = content.count("txn ") + content.count("txna ")
    num_and = content.count("&&") + content.count(" && ")
    num_or = content.count("||") + content.count(" || ")
    contract_length = len(lines)
    
    return {
        "has_rekey_check": has_rekey,
        "has_close_check": has_close,
        "has_receiver_check": has_receiver,
        "num_txn": num_txn,
        "num_and": num_and,
        "num_or": num_or,
        "contract_length": contract_length
    }
