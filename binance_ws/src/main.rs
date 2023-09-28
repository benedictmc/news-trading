// Main application of the News Trading application
// Copyright: Benedict McGovern

mod models;

use models::{BinanceMessage, TradeData, TradeInfo, TreeOfAlphaMessage, QuotedUser, Suggestion};
use std::collections::HashMap;
use tokio::time::{Duration, interval};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use url::Url;
use futures::StreamExt;
use serde::Deserialize;
use futures::SinkExt;
use std::time::SystemTime;

const SYMBOLS: [&str; 25] = [
    "BTCUSDT", "ETHUSDT",
    "APTUSDT", "ASTRUSDT", "BALUSDT", "BNBUSDT", "C98USDT",
    "CELOUSDT", "CHZUSDT", "CRVUSDT", "DOGEUSDT", "GALUSDT",
    "GTCUSDT", "HBARUSDT", "HFTUSDT", "ICPUSDT", "INJUSDT",
    "KLAYUSDT", "LEVERUSDT", "MASKUSDT", "ONTUSDT", "QTUMUSDT",
    "RLCUSDT", "THETAUSDT", "XRPUSDT"
];

const BINANCE_TICK_INTERVAL: u64 = 30;
const TOA_PING_INTERVAL: u64 = 20;

#[tokio::main]
async fn main() {
    // Run both WebSocket tasks concurrently
    tokio::join!(run_binance_websocket(), run_treeofalpha_websocket());
}

async fn run_binance_websocket() {
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
                    let avg_price = if info.count == 0 { 0.0 } else { round(info.total_price / info.count as f64 * 100.0, 6) / 100.0 };
                    // Only print if there was at least one trade.
                    if info.count > 0 {
                        let current_time = SystemTime::now()
                        .duration_since(SystemTime::UNIX_EPOCH)
                        .unwrap()
                        .as_nanos();
                        println!(
                            "> binancews: [{}] Symbol: {}, Avg Price: {}, amount_of_buys: {}, amount_of_sells: {}, Volume Bought: {}, Volume Sold: {}", 
                            current_time,
                            symbol, avg_price, info.amount_of_buys, info.amount_of_sells, info.volume_bought, info.volume_sold
                        );
                    }
                    
                }
                println!("***********");
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
                        match serde_json::from_str::<TreeOfAlphaMessage>(&text) {
                            Ok(parsed_message) => {
                                // Process the deserialized message or print it
                                println!("> treeofalpha: Received Message: {:?}", parsed_message);
                            },
                            Err(e) => {
                                println!("> treeofalpha: Failed to deserialize message: {}", e);
                            }
                        }
                    },
                    Message::Pong(pong) => {
                        println!("> treeofalpha: PONG");
                    },
                    _ => {
                        println!("> treeofalpha: Received unknown message");
                    }
                }
            },
            _ = interval_tick.tick() => {
                ws_write.send(Message::Ping(Vec::new())).await.expect("> treeofalpha: Failed to send ping to treeofalpha");
                // ws_write.send(Message::Text("ping".into())).await.expect("Failed to send ping to treeofalpha");
            },
        }
    }
}

    
fn round(x: f64, decimals: u32) -> f64 {
    let y = 10i64.pow(decimals) as f64;
    (x * y).round() / y
}