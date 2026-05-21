export interface Suggestion {
  line: number;
  type?: string;
  issue?: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  suggestion?: string;
}

export interface ScanResult {
  scan_id: string;
  score: number;
  risk_level: string;
  vulnerabilities: Suggestion[];
  contract_code: string;
  contract_hash: string;
  summary: string;
  label: string;
}

export interface AlgoShieldConfig {
  apiKey?: string;
  apiUrl?: string;
  walletAddress?: string;
  silent?: boolean;
}

export declare class AlgoShield {
  constructor(config?: AlgoShieldConfig);
  scan(contractCode: string): Promise<ScanResult>;
  scanFile(filePath: string): Promise<ScanResult>;
  scanDir(dirPath: string): Promise<ScanResult[]>;
  getReport(scanId: string): Promise<ScanResult>;
  watch(dirPath: string, options?: any): any;
}

export declare function scan(code: string, opts?: AlgoShieldConfig): Promise<ScanResult>;
export declare function scanFile(fp: string, opts?: AlgoShieldConfig): Promise<ScanResult>;
export declare function watch(dp: string, opts?: AlgoShieldConfig): any;
