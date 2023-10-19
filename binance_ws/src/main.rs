// Main application of the News Trading application
// Copyright: Benedict McGovern

mod models;

extern crate reqwest;
extern crate hex;
extern crate phf;
extern crate log;
extern crate log4rs;


use models::{BinanceMessage, TradeInfo, TreeOfAlphaTweet, TreeOfAlphaNews, TreeOfAlphaNewsVariation, TradeStats, NewsEvent, Suggestion, BinanceError, BinanceTradeInfo, SYMBOLS_INFO};
use std::collections::HashMap;
use tokio::time::{Duration, interval, sleep};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use url::Url;
use futures::StreamExt;
use futures::SinkExt;
use std::sync::{Arc};
use tokio::sync::Mutex;
use std::fs;
use std::env;
use reqwest::header::{HeaderMap, HeaderValue, CONTENT_TYPE};
use std::time::{SystemTime, UNIX_EPOCH};
use hmac::{Hmac, Mac, NewMac};
use sha2::Sha256;
use phf::phf_map;
use phf::Map;
use std::time::Instant;
use log::{error, warn, info, debug};
use std::cmp::max;
use std::collections::HashSet;

const BINANCE_TICK_INTERVAL: u64 = 1;
const TOA_PING_INTERVAL: u64 = 20;

#[tokio::main]
async fn main(){
    // Run both WebSocket tasks concurrently
    log_print("INFO", "main: > Starting WebSocket tasks...");

    log4rs::init_file("/home/ben/dev/news-trading/binance_ws/src/log4rs.yml", Default::default()).unwrap_or_else(|e| {
        eprintln!("Error initializing log4rs: {}", e);
    });

    let symbol_trade_infos = Arc::new(Mutex::new(HashMap::new()));
    let symbol_trade_stats = Arc::new(Mutex::new(HashMap::new()));
    let news_event_log = Arc::new(Mutex::new(HashMap::new()));

    for (symbol, _) in SYMBOLS_INFO.entries() {
        symbol_trade_infos.lock().await.insert(symbol.to_string(), TradeInfo::default());
        symbol_trade_stats.lock().await.insert(symbol.to_string(), TradeStats::default());
    }

    tokio::spawn(log_health_check());
    tokio::spawn(focus_new_event_log(news_event_log.clone(), symbol_trade_infos.clone(), symbol_trade_stats.clone()));
    tokio::spawn(calculate_averages(symbol_trade_infos.clone(), symbol_trade_stats.clone()));
    tokio::join!(run_binance_websocket(symbol_trade_infos.clone()), run_treeofalpha_websocket(news_event_log.clone()));
}

async fn run_binance_websocket(symbol_trade_infos: Arc<Mutex<HashMap<String, TradeInfo>>>) {

    let symbols_string = SYMBOLS_INFO.entries()
        .map(|(symbol, _)| format!("{}@aggTrade", symbol.to_lowercase()))
        .collect::<Vec<_>>()
        .join("/");

    let url_str = format!("wss://stream.binance.com:443/stream?streams={}", symbols_string);
    let url = Url::parse(&url_str).unwrap();

    let (mut ws_stream, response) = connect_async(url).await.expect("Failed to connect");

    log_print("INFO", format!("run_binance_websocket: > Connected with response: {:?}", response).as_str());

    let (mut sink, mut stream) = ws_stream.split();

    let mut interval_tick = interval(Duration::from_secs(60));

    loop {
        tokio::select! {
            Some(Ok(message)) = stream.next() => {
                match message {
                    Message::Ping(ping_data) => {
                        if let Err(e) = sink.send(Message::Pong(ping_data)).await {
                            log_print("ERROR", format!("Failed to send pong: {}", e).as_str());
                        }
                    },
                    Message::Text(text) => {
                        // Handle text messages as before
                        match serde_json::from_str::<BinanceMessage>(&text) {
                            Ok(parsed_message) => {
                                let symbol = parsed_message.data.s;
                                let mut trade_info_lock = symbol_trade_infos.lock().await;
        
                                if let Some(trade_info) = trade_info_lock.get_mut(&symbol) {
                                    trade_info.count += 1;
                                    if let (Ok(price), Ok(qty)) = (parsed_message.data.p.parse::<f64>(), parsed_message.data.q.parse::<f64>()) {
        
                                        trade_info.total_price += price;
                                        let volume = price * qty;
                                        if parsed_message.data.m {
                                            trade_info.volume_sold += volume;
                                            trade_info.amount_of_sells += 1;
                                        } else {
                                            trade_info.volume_bought += volume;
                                            trade_info.amount_of_buys += 1;
                                        }
                                    }
                                }
                            },
                            Err(e) => log_print("ERROR", format!("Failed to deserialize message: {}, text: {}", e, text).as_str()),
                        }
                    },
                    _ => log_print("ERROR", format!("Received unexpected message: {:?}", message).as_str()),
                }
            }
        }
    }
}


async fn run_treeofalpha_websocket(news_event_log: Arc<Mutex<HashMap<String, NewsEvent>>>) {
    let url = Url::parse("wss://news.treeofalpha.com/ws").unwrap();

    loop {
        match connect_async(url.clone()).await {
            Ok((ws_stream, response)) => {
                log_print("INFO", format!("Connected to treeofalpha with response: {:?}", response).as_str());

                let (mut ws_write, mut ws_read) = ws_stream.split();
                let mut interval_tick = interval(Duration::from_secs(TOA_PING_INTERVAL));

                loop {
                    tokio::select! {
                        Some(Ok(message)) = ws_read.next() => {
                            match message {
                                Message::Text(text) => {
                                    let current_time = get_current_time();
                                    match serde_json::from_str::<TreeOfAlphaNews>(&text) {
                                        Ok(news_message) => {
                                            log_print("INFO", format!("TreeOfAlphaNews: {:?}", news_message).as_str());

                                            process_suggestions(&news_message.suggestions, &news_event_log, &news_message.title, &news_message._id).await;
                                        },
                                        Err(_) => {
                                            match serde_json::from_str::<TreeOfAlphaNewsVariation>(&text) {
                                                Ok(news_variation_message) => {
                                                    log_print("INFO", format!("TreeOfAlphaNewsVariation: {:?}", news_variation_message).as_str());

                                                    process_suggestions(&news_variation_message.suggestions, &news_event_log, &news_variation_message.title, &news_variation_message._id).await;
                                                },
                                                Err(_) => {
                                                    match serde_json::from_str::<TreeOfAlphaTweet>(&text) {
                                                        Ok(tweet_message) => {
                                                            log_print("INFO", format!("TreeOfAlphaTweet: {:?}", tweet_message).as_str());

                                                            process_suggestions(&tweet_message.suggestions, &news_event_log, &tweet_message.body, &tweet_message._id).await;
                                                        },
                                                        Err(e) => {
                                                            println!("> treeofalpha: Failed to deserialize both formats: {} {}", e, text);
                                                        }
                                                    }
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
                                Ok(_) => {},
                                Err(e) => {
                                    log_print("ERROR", format!("> treeofalpha: Failed to send ping to treeofalpha: {}", e).as_str());
                                    break;  // Break inner loop to trigger reconnection
                                },
                            }
                        },
                    }
                }
            },
            Err(e) => {
                println!("Failed to connect to treeofalpha: {}", e);
            },
        }

        println!("Attempting to reconnect in 5 seconds...");
        sleep(Duration::from_secs(5)).await;  // Wait for 5 seconds before attempting to reconnect
    }
}

async fn log_health_check() {
    let mut interval = tokio::time::interval(Duration::from_secs(60));

    loop {
        interval.tick().await;
        info!("> log_health_check: Ping Event",);
    }
}

async fn calculate_averages(symbol_trade_infos: Arc<Mutex<HashMap<String, TradeInfo>>>, symbol_trade_stats: Arc<Mutex<HashMap<String, TradeStats>>>) {
    let mut interval = tokio::time::interval(Duration::from_secs(5));

    loop {
        interval.tick().await;
        let mut symbol_trade_infos_lock = symbol_trade_infos.lock().await;

        for (symbol, trade_info) in symbol_trade_infos_lock.iter_mut() {
            
            let mut trade_stats_lock = symbol_trade_stats.lock().await;

            if let Some(trade_stats) = trade_stats_lock.get_mut(symbol) {
                trade_stats.amount_of_buys.update(trade_info.amount_of_buys);
                trade_stats.amount_of_sells.update(trade_info.amount_of_sells);
                trade_stats.volume_sold.update(trade_info.volume_sold);
                trade_stats.volume_bought.update(trade_info.volume_bought);
            }
        }
        symbol_trade_infos_lock.values_mut().for_each(|info| *info = TradeInfo::default());
    }
}

async fn focus_new_event_log(news_event_log: Arc<Mutex<HashMap<String, NewsEvent>>>, symbol_trade_infos: Arc<Mutex<HashMap<String, TradeInfo>>>, symbol_trade_stats: Arc<Mutex<HashMap<String, TradeStats>>>) {
    let mut interval = tokio::time::interval(Duration::from_millis(500));
    let mut locked_symbols: HashMap<String, u128> = HashMap::new();

    loop {
        interval.tick().await;

        let mut news_event_log_lock = news_event_log.lock().await;

        if news_event_log_lock.is_empty() {
            continue;
        }

        let mut events_to_remove = Vec::new();

        let current_time = get_current_time();

        for (binance_symbol, news_event) in news_event_log_lock.iter_mut() {

            if news_event.time_to_end < current_time {
                events_to_remove.push(binance_symbol.clone());
                continue;
            }

            let symbol_trade_infos_lock = symbol_trade_infos.lock().await;

            if let Some(latest_trade_info) = symbol_trade_infos_lock.get(binance_symbol) {

                let mut trade_stats_lock = symbol_trade_stats.lock().await;

                if let Some(trade_stats) = trade_stats_lock.get_mut(binance_symbol) {
                    let current_price = latest_trade_info.total_price / latest_trade_info.count as f64;


                    if !current_price.is_nan() {
                        if news_event.start_price == 0.0{
                            news_event.start_price = current_price.clone();
                        }
                                
                        let price_diff = (current_price - news_event.start_price) / news_event.start_price ;

                        if price_diff > news_event.max_price_diff_pos {
                            news_event.max_price_diff_pos = price_diff.clone();
                        }

                        if price_diff < news_event.max_price_diff_neg {
                            news_event.max_price_diff_neg = price_diff.clone();
                        }
                    }
                    news_event.amount_of_buys_z_score = f64::max(news_event.amount_of_buys_z_score, trade_stats.amount_of_buys.z_score(latest_trade_info.amount_of_buys));
                    news_event.amount_of_sells_z_score = f64::max(news_event.amount_of_sells_z_score, trade_stats.amount_of_sells.z_score(latest_trade_info.amount_of_sells));
                    news_event.volume_sold_z_score = f64::max(news_event.volume_sold_z_score, trade_stats.volume_sold.z_score(latest_trade_info.volume_sold));
                    news_event.volume_bought_z_score = f64::max(news_event.volume_bought_z_score, trade_stats.volume_bought.z_score(latest_trade_info.volume_bought));

                    let total_zscore = news_event.amount_of_buys_z_score + news_event.amount_of_sells_z_score + news_event.volume_sold_z_score + news_event.volume_bought_z_score;
                    news_event.total_z_score = f64::max(news_event.total_z_score, total_zscore.clone());

                    if total_zscore > 100.0{
                        

                        match locked_symbols.get(binance_symbol) {
                            Some(&timestamp) => {
                                if current_time > timestamp {
                                    locked_symbols.remove(binance_symbol);
                                } else {
                                    continue;
                                }
                            },
                            None => {}
                        }

                        println!("*******");
                        println!("> focus_new_event_log: binance_symbol: {}", binance_symbol);
                        println!("> focus_new_event_log: News event title {}", news_event.news_title);
                        println!("> focus_new_event_log: GOING TO TRADE!!");
                        println!("> focus_new_event_log: Time is {}", get_current_time());

                        let price_precision = match SYMBOLS_INFO.get(&binance_symbol) {
                            Some(symbol_info) => symbol_info.price_precision as u32,
                            None => 4, // Default value if the symbol is not found
                        };

                        println!("> focus_new_event_log: Precision of {}: {}", &binance_symbol, price_precision);

                        let trade_price = round(latest_trade_info.total_price / latest_trade_info.count as f64, price_precision);
                        let trade_direction = if trade_price < news_event.start_price { "SELL" } else { "BUY" };
                        
                        println!("> focus_new_event_log: trade_direction: {}", &trade_direction);
                        println!("> focus_new_event_log: trade_price: {}", &trade_price);

                        let sl_price = if trade_direction == "SELL" {round(trade_price * 1.02, price_precision)} else { round(trade_price * 0.98, price_precision) };
                        let tp_price = if trade_direction == "SELL" {round(trade_price * 0.95, price_precision)} else { round(trade_price * 1.05, price_precision) };

                        println!("> focus_new_event_log: sl_price: {}", &sl_price);
                        println!("> focus_new_event_log: tp_price: {}", &tp_price);

                        send_futures_order(binance_symbol, trade_direction, "LIMIT",  200.0, trade_price, 5, sl_price, tp_price, news_event.news_id.as_str(), total_zscore).await;
                        let timestamp = get_current_time() + 1800000000000; // Plus 30 minutes
                        
                        locked_symbols.insert(binance_symbol.clone(), timestamp);
                    }
                }
            }
        }

        drop(news_event_log_lock);
        let mut news_event_log_lock = news_event_log.lock().await;

        for key in events_to_remove {

            if let Some(news_event) = news_event_log_lock.get_mut(&key){
                println!("> focus_new_event_log: Saving news event to file");
                log_print("INFO", format!("news_event: {:?}", news_event).as_str());
                // save_news_event_to_file(news_event).await;
            }
            news_event_log_lock.remove(&key);
        }
    }
}

async fn process_suggestions(suggestions: &[Suggestion], news_event_log: &Arc<Mutex<HashMap<String, NewsEvent>>>, title: &str, news_id: &str ) {
    for suggestion in suggestions {
        for symbols in &suggestion.symbols {
            if symbols.get("exchange") == Some(&"binance-futures".to_string()) {
                if let Some(exchange_symbol) = symbols.get("symbol") {
                    let binance_symbol = exchange_symbol.to_string();
                    let mut lock = news_event_log.lock().await;
                    if let Some(news_event) = lock.get_mut(&binance_symbol) {
                        news_event.news_occurance += 1;
                        news_event.time_to_end = get_current_time() + 60000000000 // Plus 1 minutes;
                    } else {
                        let news_event = NewsEvent {
                            binance_symbol: binance_symbol.clone(),
                            time_started: get_current_time(),
                            news_occurance: 1,
                            news_title: title.to_string(),
                            time_to_end: get_current_time() + 60000000000, // Plus 1 minutes
                            start_price: 0.0,
                            max_price_diff_neg: 100.0,
                            max_price_diff_pos: 0.0,
                            amount_of_buys_z_score: 0.0,
                            amount_of_sells_z_score: 0.0,
                            volume_sold_z_score: 0.0,
                            volume_bought_z_score: 0.0,
                            total_z_score: 0.0,
                            news_id: news_id.to_string(),
                        };
                        lock.insert(binance_symbol, news_event);
                    }
                }
            }
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

async fn save_news_event_to_file(news_event: &NewsEvent) -> Result<(), Box<dyn std::error::Error>> {
    // Serialize the struct to a JSON string
    let time_started = news_event.time_started;
    let binance_symbol = news_event.binance_symbol.clone();

    let json = serde_json::to_string_pretty(news_event)?;
    let file_path = format!("news_events/{}{}.json", time_started, binance_symbol);
    // Write the JSON string to a file
    fs::write(file_path, json)?;

    Ok(())
}

async fn send_futures_order(
    symbol: &str,
    side: &str,
    type_: &str,
    quantity: f64,
    price: f64,
    leverage: i32,
    stop_loss_price: f64,
    take_profit_price: f64,
    news_id: &str,
    z_score: f64,
) -> Result<(), reqwest::Error> {

    let api_key = env::var("BINANCE_API_KEY").expect("API_KEY not set");
    let api_secret = env::var("BINANCE_API_SECRET").expect("API_SECRET not set");
    
    // To change leverage
    let leverage_result = change_leverage(&symbol, leverage).await;

    if let Err(e) = leverage_result {
        eprintln!("Failed to change leverage: {}", e);
        return Err(e);
    }

    let opposite_side = if side == "BUY" { "SELL" } else { "BUY" };

    let quantity_precision = match SYMBOLS_INFO.get(&symbol) {
        Some(symbol_info) => symbol_info.quantity_precision as u32,
        None => 4, // Default value if the symbol is not found
    };

    println!("> send_futures_order: Current Time: {}", get_current_time());
    println!("> send_futures_order: Quantity Percision: {}", quantity_precision);

    let symbol_amount = round((quantity / price)*leverage as f64, quantity_precision);

    println!("> send_futures_order: symbol_amount: {}", symbol_amount);
    
    let timestamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_millis();

    let params = format!(
        "symbol={}&side={}&type={}&quantity={}&price={}&timeInForce=GTC&timestamp={}",
        symbol, side, type_, symbol_amount, price, timestamp
    );
    submit_trade(&params).await;


    let stop_loss_params = format!(
        "symbol={}&side={}&type=STOP_MARKET&quantity={:.2}&stopPrice={:.2}&timeInForce=GTC&timestamp={}",
        symbol, opposite_side, symbol_amount, stop_loss_price, timestamp
    );
    submit_trade(&stop_loss_params).await;


    // let take_profit_params = format!(
    //     "symbol={}&side={}&type=TAKE_PROFIT_MARKET&quantity={:.2}&stopPrice={:.2}&timeInForce=GTC&timestamp={}",
    //     symbol, opposite_side, symbol_amount, take_profit_price, timestamp
    // );
    // submit_trade(&take_profit_params).await;


    let binance_trade_info = BinanceTradeInfo {
        news_id: news_id.to_string(),
        z_score: z_score,
        symbol: symbol.to_string(),
        price: price,
        side: side.to_string(),
        quantity: symbol_amount,
        leverage: leverage,
        stop_loss_price: stop_loss_price,
        take_profit_price: take_profit_price,
    };

    log_print("INFO", format!("send_futures_order: > Sent trade: {:?}", binance_trade_info).as_str());

    Ok(())
}


async fn change_leverage(symbol: &str, leverage: i32) -> Result<(), reqwest::Error> {
    let client = reqwest::Client::new();

    let api_key = env::var("BINANCE_API_KEY").expect("API_KEY not set");
    let api_secret = env::var("BINANCE_API_SECRET").expect("API_SECRET not set");

    let timestamp = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_millis();

    // Change the leverage to 5x
    let leverage_params = format!("symbol={}&leverage={}&timestamp={}", symbol, leverage, timestamp);
    let leverage_signature = get_signature(&api_secret, &leverage_params);

    let mut headers = HeaderMap::new();
    headers.insert("X-MBX-APIKEY", HeaderValue::from_str(&api_key).unwrap());
    headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/x-www-form-urlencoded"));

    let change_leverage_url = format!("https://fapi.binance.com/fapi/v1/leverage?{}&signature={}", leverage_params, leverage_signature);

    let change_leverage_response = client.post(&change_leverage_url).headers(headers).send().await?;

    // Check for errors in the response
    if change_leverage_response.status().is_success() {
        println!("Leverage changed successfully");
        Ok(())
    } else {
        // Output the error message from Binance
        let error_msg: BinanceError = change_leverage_response.json().await?;
        println!("Failed to change leverage: {}", error_msg.msg);
        Ok(())
    }
}


async fn submit_trade(params: &str) -> Result<(), reqwest::Error>{
    let client = reqwest::Client::new();
    
    let api_key = env::var("BINANCE_API_KEY").expect("API_KEY not set");
    let api_secret = env::var("BINANCE_API_SECRET").expect("API_SECRET not set");
   
    let signature = get_signature(&api_secret, &params);

    println!("> submit_trade: signature: {}", signature);

    let mut headers = HeaderMap::new();
    headers.insert("X-MBX-APIKEY", HeaderValue::from_str(&api_key).unwrap());
    headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/x-www-form-urlencoded"));
    
    let url = format!("https://fapi.binance.com/fapi/v1/order?{}&signature={}", params, signature);
    println!("url: {}", url);
    
    let response = client.post(&url).headers(headers).send().await?;
    
    if response.status().is_success() {
        println!("> submit_trade: Order placed successfully");
    } else {
        // The request failed, print the error message
        let error_text = response.text().await?;
        println!("> submit_trade: Error: {}", error_text);
    }

    Ok(())
}


fn get_signature(api_secret: &str, request: &str) -> String {
    let mut signed_key = Hmac::<Sha256>::new_from_slice(api_secret.as_bytes()).unwrap();
    signed_key.update(request.as_bytes());
    let signature = hex::encode(signed_key.finalize().into_bytes());
    signature
}


fn log_print(log_level: &str, message: &str) {
    println!("> {}", message);

    if log_level == "ERROR" {
        error!("> {}", message);
    } else if log_level == "INFO" {
        info!("> {}", message);
    } 
}