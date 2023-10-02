// Main application of the News Trading application
// Copyright: Benedict McGovern

mod models;

use models::{BinanceMessage, TradeInfo, TreeOfAlphaTweet, TreeOfAlphaNews, SymbolTradeData, SymbolTradeTotals, TradeTotal, SymbolTradeAverages, TradeAverage};
use std::collections::HashMap;
use tokio::time::{Duration, interval};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use url::Url;
use futures::StreamExt;
use futures::SinkExt;
use std::time::SystemTime;
use std::sync::{Arc};
use tokio::sync::Mutex;

// const SYMBOLS: [&str; 25] = [
//     "BTCUSDT", "ETHUSDT",
//     "APTUSDT", "ASTRUSDT", "BALUSDT", "BNBUSDT", "C98USDT",
//     "CELOUSDT", "CHZUSDT", "CRVUSDT", "DOGEUSDT", "GALUSDT",
//     "GTCUSDT", "HBARUSDT", "HFTUSDT", "ICPUSDT", "INJUSDT",
//     "KLAYUSDT", "LEVERUSDT", "MASKUSDT", "ONTUSDT", "QTUMUSDT",
//     "RLCUSDT", "THETAUSDT", "XRPUSDT"
// ];

const SYMBOLS: [&str; 2] = [
    "BTCUSDT", "ETHUSDT"
];

const BINANCE_TICK_INTERVAL: u64 = 1;
const TOA_PING_INTERVAL: u64 = 20;


#[tokio::main]
async fn main() {
    // Run both WebSocket tasks concurrently
    println!("> Starting WebSocket tasks...");
    let symbol_trade_totals = Arc::new(Mutex::new(SymbolTradeTotals::default()));
    let symbol_trade_averages = Arc::new(Mutex::new(SymbolTradeAverages::default()));

    for &symbol in SYMBOLS.iter() {
        symbol_trade_totals.lock().await.insert(symbol.to_string(), TradeTotal::default());
        symbol_trade_averages.lock().await.insert(symbol.to_string(), TradeAverage::default());
    }

    tokio::spawn(calculate_averages(symbol_trade_averages.clone(), symbol_trade_totals.clone()));

    tokio::join!(run_binance_websocket(symbol_trade_totals.clone()), run_treeofalpha_websocket());
}

async fn run_binance_websocket(symbol_trade_totals: Arc<Mutex<SymbolTradeTotals>>) {

    let symbols_string = SYMBOLS.iter()
    .map(|s| format!("{}@aggTrade", s.to_lowercase()))
    .collect::<Vec<_>>()
    .join("/");

    let url_str = format!("wss://stream.binance.com:443/stream?streams={}", symbols_string);
    let url = Url::parse(&url_str).unwrap();

    let (ws_stream, response) = connect_async(url).await.expect("Failed to connect");

    println!("Connected with response: {:?}", response);
    let mut stream = ws_stream.split().1;  // Just using the stream part.

    let mut trade_infos: HashMap<String, TradeInfo> = SYMBOLS.iter().map(|&s| (s.to_string(), TradeInfo::default())).collect();

    let mut interval_tick = interval(Duration::from_secs(BINANCE_TICK_INTERVAL));

    loop {
        tokio::select! {
            Some(Ok(message)) = stream.next() => {

                if let Message::Text(text) = message {

                    match serde_json::from_str::<BinanceMessage>(&text) {
                        Ok(parsed_message) => {

                            let symbol = parsed_message.data.s;

                            if let Some(info) = trade_infos.get_mut(&symbol) {
                                info.count += 1;

                                if let (Ok(price), Ok(qty)) = (parsed_message.data.p.parse::<f64>(), parsed_message.data.q.parse::<f64>()) {

                                    info.total_price += price;
                                    let volume = price * qty;
                                    if parsed_message.data.m {
                                        info.volume_sold += volume;
                                        info.amount_of_sells += 1;
                                    } else {
                                        info.volume_bought += volume;
                                        info.amount_of_buys += 1;
                                    }
                                }
                            }
                        },
                        Err(_) => println!("> binancews: Failed to deserialize message"),
                    }
                }
            },
            _ = interval_tick.tick() => {
                for (symbol, info) in &trade_infos {
                    
                    let mut trade_total_lock = symbol_trade_totals.lock().await;
                    if let Some(trade_total) = trade_total_lock.get_mut(symbol) {

                        trade_total.total_volume_sold += info.volume_sold;
                        trade_total.total_amount_of_sells += info.amount_of_sells;
                        trade_total.total_volume_bought += info.volume_bought;
                        trade_total.total_amount_of_buys += info.amount_of_buys;
    
                        trade_total.times_updated += 1;
                        // println!("> binancews: Updated totals for {}", symbol);
                        // println!("> binancews: Total volume sold: {}", trade_total.total_volume_sold);
                        // println!("> binancews: Total amount of sells: {}", trade_total.total_amount_of_sells);
                        // println!("> binancews: Total volume bought: {}", trade_total.total_volume_bought);
                        // println!("> binancews: Total amount of buys: {}", trade_total.total_amount_of_buys);
                        // println!("> binancews: Times updated: {}", trade_total.times_updated);
                        // println!("***********");
                    }
                }
                trade_infos.values_mut().for_each(|info| *info = TradeInfo::default());
            },
        }
    }
}

async fn run_treeofalpha_websocket() {
    let url = Url::parse("wss://news.treeofalpha.com/ws").unwrap();

    let (mut ws_stream, response) = connect_async(url).await.expect("Failed to connect to treeofalpha");
    println!("Connected to treeofalpha with response: {:?}", response);

    let (mut ws_write, mut ws_read) = ws_stream.split();

    let mut interval_tick = interval(Duration::from_secs(TOA_PING_INTERVAL));

    loop {
        tokio::select! {
            Some(Ok(message)) = ws_read.next() => {
                match message {
                    Message::Text(text) => {
                        // First, try to parse as TreeOfAlphaTweet
                        match serde_json::from_str::<TreeOfAlphaNews>(&text) {
                            Ok(news_message) => {
                                let current_time = get_current_time();
                                println!("> treeofalpha: Received news at {}: {:?}", current_time, news_message);
                            },
                            Err(_) => {
                                match serde_json::from_str::<TreeOfAlphaTweet>(&text) {
                                    Ok(tweet_message) => {
                                        let current_time = get_current_time();
                                        println!("> treeofalpha: Received tweet at {}: {:?}", current_time, tweet_message);
                                    },
                                    Err(e) => {
                                        println!("> treeofalpha: Failed to deserialize both formats: {}", e);
                                    }
                                }
                            }
                        }
                    },
                    Message::Pong(_) => {
                        // No message for now
                    },
                    _ => {}
                }
            },
            _ = interval_tick.tick() => {
                match ws_write.send(Message::Ping(Vec::new())).await {
                    Ok(_) => println!("> treeofalpha: Ping sent successfully"),
                    Err(e) => println!("> treeofalpha: Failed to send ping to treeofalpha: {}", e),
                }
            },
        }
    }
}



async fn calculate_averages(symbol_trade_averages: Arc<Mutex<SymbolTradeAverages>>, symbol_trade_totals: Arc<Mutex<SymbolTradeTotals>>) {
    let mut interval = tokio::time::interval(Duration::from_secs(60));

    loop {
        interval.tick().await;

        let mut trade_averages = symbol_trade_averages.lock().await;
        let mut trade_total_lock = symbol_trade_totals.lock().await;

        for (symbol, trade_average) in trade_averages.iter_mut() {

            if let Some(trade_total) = trade_total_lock.get_mut(symbol) {
                let times_updated = trade_total.times_updated;

                if times_updated != 0 {
                    trade_average.avg_volume_sold = trade_total.total_volume_sold / (times_updated as f64);
                    trade_average.avg_amount_of_sells = (trade_total.total_amount_of_sells as f64 / times_updated as f64);
                    trade_average.avg_volume_bought = trade_total.total_volume_bought / (times_updated as f64);
                    trade_average.avg_amount_of_buys = (trade_total.total_amount_of_buys as f64 / times_updated as f64);
                } 
            }
            println!("> calculate_averages: Averages for {}:", symbol);
            println!("> calculate_averages: Average volume sold: {}", trade_average.avg_volume_sold);
            println!("> calculate_averages: Average amount of sells: {}", trade_average.avg_amount_of_sells);
            println!("> calculate_averages: Average volume bought: {}", trade_average.avg_volume_bought);
            println!("> calculate_averages: Average amount of buys: {}", trade_average.avg_amount_of_buys);

        }
    }
}


//  Helper functions
fn round(x: f64, decimals: u32) -> f64 {
    let y = 10i64.pow(decimals) as f64;
    (x * y).round() / y
}

fn get_current_time() -> u128 {
    SystemTime::now()
    .duration_since(SystemTime::UNIX_EPOCH)
    .unwrap()
    .as_nanos()
}