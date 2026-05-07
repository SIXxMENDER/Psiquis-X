use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::env;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::Path;

#[derive(Debug, Deserialize)]
struct Candle {
    timestamp: u64,
    open: f64,
    high: f64,
    low: f64,
    close: f64,
    volume: f64,
}

#[derive(Serialize)]
struct SimulationResult {
    total_trades: usize,
    winning_trades: usize,
    win_rate: f64,
    net_profit_percent: f64,
    max_drawdown_percent: f64,
    sharpe_ratio: f64,
}

#[derive(Serialize, Deserialize)]
struct Block {
    block_id: usize,
    timestamp: u64,
    previous_hash: String,
    merkle_root: String,
    parameters: serde_json::Value,
    results: serde_json::Value,
    quant_consensus: serde_json::Value,
    hash: String,
}

fn double_sha256(data: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data.as_bytes());
    let hash1 = hasher.finalize();
    
    let mut hasher2 = Sha256::new();
    hasher2.update(hash1);
    hex::encode(hasher2.finalize())
}

fn calculate_merkle_root(leaves: Vec<String>) -> String {
    if leaves.is_empty() {
        return String::new();
    }
    if leaves.len() == 1 {
        return leaves[0].clone();
    }
    
    let mut current_level = leaves;
    while current_level.len() > 1 {
        let mut next_level = Vec::new();
        for i in (0..current_level.len()).step_by(2) {
            let left = &current_level[i];
            let right = if i + 1 < current_level.len() {
                &current_level[i + 1]
            } else {
                &current_level[i] // Duplicate last if odd
            };
            let combined = format!("{}{}", left, right);
            next_level.push(double_sha256(&combined));
        }
        current_level = next_level;
    }
    current_level[0].clone()
}

fn calculate_ema(prices: &[f64], period: usize) -> Vec<f64> {
    let mut ema = vec![0.0; prices.len()];
    if prices.is_empty() { return ema; }
    
    let multiplier = 2.0 / (period as f64 + 1.0);
    ema[0] = prices[0];
    
    for i in 1..prices.len() {
        ema[i] = (prices[i] - ema[i - 1]) * multiplier + ema[i - 1];
    }
    ema
}

// A simple backtest loop to demonstrate the speed of Rust
fn run_simulation(csv_path: &str, p_ema_short: usize, p_ema_mid: usize, _p_ema_long: usize, _p_ema_trend: usize) {
    let mut reader = csv::Reader::from_path(csv_path).expect("Cannot read CSV");
    let mut candles: Vec<Candle> = Vec::new();
    let mut closes: Vec<f64> = Vec::new();

    for result in reader.deserialize() {
        let candle: Candle = result.expect("Cannot parse candle");
        closes.push(candle.close);
        candles.push(candle);
    }

    let ema_short = calculate_ema(&closes, p_ema_short);
    let ema_mid = calculate_ema(&closes, p_ema_mid);

    let mut in_position = false;
    let mut entry_price = 0.0;
    
    let mut winning_trades = 0;
    let mut total_trades = 0;
    let mut net_profit = 0.0; // percent
    
    // Very basic crossover strategy for the demo
    for i in 1..closes.len() {
        let prev_short = ema_short[i-1];
        let prev_mid = ema_mid[i-1];
        let curr_short = ema_short[i];
        let curr_mid = ema_mid[i];

        // Cross up
        if !in_position && prev_short <= prev_mid && curr_short > curr_mid {
            in_position = true;
            entry_price = closes[i];
        } 
        // Cross down
        else if in_position && prev_short >= prev_mid && curr_short < curr_mid {
            in_position = false;
            let exit_price = closes[i];
            let profit_pct = (exit_price - entry_price) / entry_price * 100.0;
            
            net_profit += profit_pct;
            total_trades += 1;
            if profit_pct > 0.0 {
                winning_trades += 1;
            }
        }
    }

    let win_rate = if total_trades > 0 {
        (winning_trades as f64 / total_trades as f64) * 100.0
    } else {
        0.0
    };

    // Mocking Sharpe/Drawdown for the sake of the demo's simplicity,
    // though in a real engine you'd calculate the standard deviation of returns.
    let sharpe_ratio = if win_rate > 50.0 { 1.5 + (net_profit / 100.0) } else { 0.5 };
    let max_drawdown_percent = 15.0 - (win_rate / 10.0);

    let result = SimulationResult {
        total_trades,
        winning_trades,
        win_rate,
        net_profit_percent: net_profit,
        max_drawdown_percent,
        sharpe_ratio,
    };

    let json_output = serde_json::to_string(&result).unwrap();
    println!("{}", json_output);
}

fn seal_block(ledger_path: &str, params_json: &str, results_json: &str, consensus_json: &str) {
    let mut blocks: Vec<Block> = Vec::new();
    
    if Path::new(ledger_path).exists() {
        let content = fs::read_to_string(ledger_path).unwrap_or_else(|_| "[]".to_string());
        blocks = serde_json::from_str(&content).unwrap_or_default();
    }

    let previous_hash = if blocks.is_empty() {
        "0000000000000000000000000000000000000000000000000000000000000000".to_string()
    } else {
        blocks.last().unwrap().hash.clone()
    };

    let params: serde_json::Value = serde_json::from_str(params_json).unwrap_or(json!({}));
    let results: serde_json::Value = serde_json::from_str(results_json).unwrap_or(json!({}));
    let consensus: serde_json::Value = serde_json::from_str(consensus_json).unwrap_or(json!({}));
    
    let block_id = blocks.len();
    let timestamp = std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_secs();

    // Merkle Tree calculation
    let hash_params = double_sha256(&params.to_string());
    let hash_results = double_sha256(&results.to_string());
    let hash_consensus = double_sha256(&consensus.to_string());
    
    let leaves = vec![hash_params, hash_results, hash_consensus];
    let merkle_root = calculate_merkle_root(leaves);

    // The data to hash for the block header
    let data_to_hash = format!("{}{}{}{}", block_id, timestamp, previous_hash, merkle_root);
    
    let hash_hex = double_sha256(&data_to_hash);

    let new_block = Block {
        block_id,
        timestamp,
        previous_hash,
        merkle_root,
        parameters: params,
        results,
        quant_consensus: consensus,
        hash: hash_hex.clone(),
    };

    blocks.push(new_block);

    let mut file = OpenOptions::new()
        .write(true)
        .create(true)
        .truncate(true)
        .open(ledger_path)
        .expect("Cannot open ledger file");
        
    let json_out = serde_json::to_string_pretty(&blocks).unwrap();
    file.write_all(json_out.as_bytes()).expect("Cannot write to ledger");

    println!("{{\"status\": \"success\", \"sealed_hash\": \"{}\"}}", hash_hex);
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: rust_core <command> [args...]");
        std::process::exit(1);
    }

    let command = &args[1];

    match command.as_str() {
        "run_simulation" => {
            // Args: run_simulation <csv> <ema_short> <ema_mid> <ema_long> <ema_trend>
            if args.len() < 7 {
                eprintln!("Missing arguments for run_simulation");
                std::process::exit(1);
            }
            let csv_path = &args[2];
            let ema_short: usize = args[3].parse().unwrap_or(3);
            let ema_mid: usize = args[4].parse().unwrap_or(12);
            let ema_long: usize = args[5].parse().unwrap_or(21);
            let ema_trend: usize = args[6].parse().unwrap_or(200);

            run_simulation(csv_path, ema_short, ema_mid, ema_long, ema_trend);
        }
        "seal_block" => {
            // Args: seal_block <ledger_path> <params_json> <results_json> <consensus_json>
            if args.len() < 6 {
                eprintln!("Missing arguments for seal_block");
                std::process::exit(1);
            }
            let ledger_path = &args[2];
            let params = &args[3];
            let results = &args[4];
            let consensus = &args[5];

            seal_block(ledger_path, params, results, consensus);
        }
        _ => {
            eprintln!("Unknown command: {}", command);
            std::process::exit(1);
        }
    }
}
