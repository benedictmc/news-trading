// Main application of the News Trading application
// Copyright: Benedict McGovern

mod models;

use models::{BinanceMessage, TradeInfo, TreeOfAlphaTweet, TreeOfAlphaNews, TreeOfAlphaNewsVariation, TradeStats, NewsEvent, Suggestion};
use std::collections::HashMap;
use tokio::time::{Duration, interval, sleep};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use url::Url;
use futures::StreamExt;
use futures::SinkExt;
use std::time::SystemTime;
use std::sync::{Arc};
use tokio::sync::Mutex;
use std::fs;

// const SYMBOLS: [&str; 25] = [
//     "BTCUSDT", "ETHUSDT",
//     "APTUSDT", "ASTRUSDT", "BALUSDT", "BNBUSDT", "C98USDT",
//     "CELOUSDT", "CHZUSDT", "CRVUSDT", "DOGEUSDT", "GALUSDT",
//     "GTCUSDT", "HBARUSDT", "HFTUSDT", "ICPUSDT", "INJUSDT",
//     "KLAYUSDT", "LEVERUSDT", "MASKUSDT", "ONTUSDT", "QTUMUSDT",
//     "RLCUSDT", "THETAUSDT", "XRPUSDT"
// ];


const SYMBOLS: [&str; 213] = [
    "BTCUSDT",
    "ETHUSDT",
    "BCHUSDT",
    "XRPUSDT",
    "EOSUSDT",
    "LTCUSDT",
    "TRXUSDT",
    "ETCUSDT",
    "LINKUSDT",
    "XLMUSDT",
    "ADAUSDT",
    "XMRUSDT",
    "DASHUSDT",
    "ZECUSDT",
    "XTZUSDT",
    "BNBUSDT",
    "ATOMUSDT",
    "ONTUSDT",
    "IOTAUSDT",
    "BATUSDT",
    "VETUSDT",
    "NEOUSDT",
    "QTUMUSDT",
    "IOSTUSDT",
    "THETAUSDT",
    "ALGOUSDT",
    "ZILUSDT",
    "KNCUSDT",
    "ZRXUSDT",
    "COMPUSDT",
    "OMGUSDT",
    "DOGEUSDT",
    "SXPUSDT",
    "KAVAUSDT",
    "BANDUSDT",
    "RLCUSDT",
    "WAVESUSDT",
    "MKRUSDT",
    "SNXUSDT",
    "DOTUSDT",
    "DEFIUSDT",
    "YFIUSDT",
    "BALUSDT",
    "CRVUSDT",
    "TRBUSDT",
    "RUNEUSDT",
    "SUSHIUSDT",
    "SRMUSDT",
    "EGLDUSDT",
    "SOLUSDT",
    "ICXUSDT",
    "STORJUSDT",
    "BLZUSDT",
    "UNIUSDT",
    "AVAXUSDT",
    "FTMUSDT",
    "HNTUSDT",
    "ENJUSDT",
    "FLMUSDT",
    "TOMOUSDT",
    "RENUSDT",
    "KSMUSDT",
    "NEARUSDT",
    "AAVEUSDT",
    "FILUSDT",
    "RSRUSDT",
    "LRCUSDT",
    "MATICUSDT",
    "OCEANUSDT",
    "CVCUSDT",
    "BELUSDT",
    "CTKUSDT",
    "AXSUSDT",
    "ALPHAUSDT",
    "ZENUSDT",
    "SKLUSDT",
    "GRTUSDT",
    "1INCHUSDT",
    "CHZUSDT",
    "SANDUSDT",
    "ANKRUSDT",
    "BTSUSDT",
    "LITUSDT",
    "UNFIUSDT",
    "REEFUSDT",
    "RVNUSDT",
    "SFPUSDT",
    "XEMUSDT",
    "BTCSTUSDT",
    "COTIUSDT",
    "CHRUSDT",
    "MANAUSDT",
    "ALICEUSDT",
    "HBARUSDT",
    "ONEUSDT",
    "LINAUSDT",
    "STMXUSDT",
    "DENTUSDT",
    "CELRUSDT",
    "HOTUSDT",
    "MTLUSDT",
    "OGNUSDT",
    "NKNUSDT",
    "SCUSDT",
    "DGBUSDT",
    "1000SHIBUSDT",
    "BAKEUSDT",
    "GTCUSDT",
    "BTCDOMUSDT",
    "IOTXUSDT",
    "AUDIOUSDT",
    "RAYUSDT",
    "C98USDT",
    "MASKUSDT",
    "ATAUSDT",
    "DYDXUSDT",
    "1000XECUSDT",
    "GALAUSDT",
    "CELOUSDT",
    "ARUSDT",
    "KLAYUSDT",
    "ARPAUSDT",
    "CTSIUSDT",
    "LPTUSDT",
    "ENSUSDT",
    "PEOPLEUSDT",
    "ANTUSDT",
    "ROSEUSDT",
    "DUSKUSDT",
    "FLOWUSDT",
    "IMXUSDT",
    "API3USDT",
    "GMTUSDT",
    "APEUSDT",
    "WOOUSDT",
    "FTTUSDT",
    "JASMYUSDT",
    "DARUSDT",
    "GALUSDT",
    "OPUSDT",
    "INJUSDT",
    "STGUSDT",
    "FOOTBALLUSDT",
    "SPELLUSDT",
    "1000LUNCUSDT",
    "LUNA2USDT",
    "LDOUSDT",
    "CVXUSDT",
    "ICPUSDT",
    "APTUSDT",
    "QNTUSDT",
    "BLUEBIRDUSDT",
    "FETUSDT",
    "FXSUSDT",
    "HOOKUSDT",
    "MAGICUSDT",
    "TUSDT",
    "RNDRUSDT",
    "HIGHUSDT",
    "MINAUSDT",
    "ASTRUSDT",
    "AGIXUSDT",
    "PHBUSDT",
    "GMXUSDT",
    "CFXUSDT",
    "STXUSDT",
    "COCOSUSDT",
    "BNXUSDT",
    "ACHUSDT",
    "SSVUSDT",
    "CKBUSDT",
    "PERPUSDT",
    "TRUUSDT",
    "LQTYUSDT",
    "USDCUSDT",
    "IDUSDT",
    "ARBUSDT",
    "JOEUSDT",
    "TLMUSDT",
    "AMBUSDT",
    "LEVERUSDT",
    "RDNTUSDT",
    "HFTUSDT",
    "XVSUSDT",
    "BLURUSDT",
    "EDUUSDT",
    "IDEXUSDT",
    "SUIUSDT",
    "1000PEPEUSDT",
    "1000FLOKIUSDT",
    "UMAUSDT",
    "RADUSDT",
    "KEYUSDT",
    "COMBOUSDT",
    "NMRUSDT",
    "MAVUSDT",
    "MDTUSDT",
    "XVGUSDT",
    "WLDUSDT",
    "PENDLEUSDT",
    "ARKMUSDT",
    "AGLDUSDT",
    "YGGUSDT",
    "DODOXUSDT",
    "BNTUSDT",
    "OXTUSDT",
    "SEIUSDT",
    "CYBERUSDT",
    "HIFIUSDT",
    "ARKUSDT",
    "FRONTUSDT",
    "GLMRUSDT",
    "BICOUSDT"
];

// const SYMBOLS: [&str; 2] = [
//     "BTCUSDT", "ETHUSDT"
// ];

const BINANCE_TICK_INTERVAL: u64 = 1;
const TOA_PING_INTERVAL: u64 = 20;


#[tokio::main]
async fn main() {
    // Run both WebSocket tasks concurrently
    println!("> Starting WebSocket tasks...");
    let symbol_trade_infos = Arc::new(Mutex::new(HashMap::new()));
    let symbol_trade_stats = Arc::new(Mutex::new(HashMap::new()));
    let news_event_log = Arc::new(Mutex::new(HashMap::new()));

    for &symbol in SYMBOLS.iter() {
        symbol_trade_infos.lock().await.insert(symbol.to_string(), TradeInfo::default());
        symbol_trade_stats.lock().await.insert(symbol.to_string(), TradeStats::default());
    }
    tokio::spawn(focus_new_event_log(news_event_log.clone(), symbol_trade_infos.clone(), symbol_trade_stats.clone()));
    tokio::spawn(calculate_averages(symbol_trade_infos.clone(), symbol_trade_stats.clone()));
    tokio::join!(run_binance_websocket(symbol_trade_infos.clone()), run_treeofalpha_websocket(news_event_log.clone()));
}


async fn run_binance_websocket(symbol_trade_infos: Arc<Mutex<HashMap<String, TradeInfo>>>) {

    let symbols_string = SYMBOLS.iter()
    .map(|s| format!("{}@aggTrade", s.to_lowercase()))
    .collect::<Vec<_>>()
    .join("/");

    let url_str = format!("wss://stream.binance.com:443/stream?streams={}", symbols_string);
    let url = Url::parse(&url_str).unwrap();

    let (ws_stream, response) = connect_async(url).await.expect("Failed to connect");

    println!("Connected with response: {:?}", response);
    let mut stream = ws_stream.split().1;  // Just using the stream part.

    loop {
        tokio::select! {
            Some(Ok(message)) = stream.next() => {
                let start_current_time = get_current_time();
                if let Message::Text(text) = message {

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
                        Err(_) => println!("> binancews: Failed to deserialize message"),
                    }
                }
                // let end_current_time = get_current_time();
                // println!("> binancews: Updated averages in {}ns", end_current_time - start_current_time); // Average is 15000ns
            }
        }
    }
}

async fn run_treeofalpha_websocket(news_event_log: Arc<Mutex<HashMap<String, NewsEvent>>>) {
    let url = Url::parse("wss://news.treeofalpha.com/ws").unwrap();

    loop {
        match connect_async(url.clone()).await {
            Ok((ws_stream, response)) => {
                println!("Connected to treeofalpha with response: {:?}", response);

                let (mut ws_write, mut ws_read) = ws_stream.split();
                let mut interval_tick = interval(Duration::from_secs(TOA_PING_INTERVAL));

                loop {
                    tokio::select! {
                        Some(Ok(message)) = ws_read.next() => {
                            match message {
                                Message::Text(text) => {
                                    match serde_json::from_str::<TreeOfAlphaNews>(&text) {
                                        Ok(news_message) => {
                                            let current_time = get_current_time();
                                            println!("> treeofalpha: Received news at {}: {:?}", current_time, news_message);
                                            process_suggestions(&news_message.suggestions, &news_event_log, &news_message.title).await;
                                        },
                                        Err(_) => {
                                            match serde_json::from_str::<TreeOfAlphaNewsVariation>(&text) {
                                                Ok(news_variation_message) => {
                                                    let current_time = get_current_time();
                                                    println!("> treeofalpha: Received news at {}: {:?}", current_time, news_variation_message);
                                                    process_suggestions(&news_variation_message.suggestions, &news_event_log, &news_variation_message.title).await;
                                                },
                                                Err(_) => {
                                                    match serde_json::from_str::<TreeOfAlphaTweet>(&text) {
                                                        Ok(tweet_message) => {
                                                            let current_time = get_current_time();
                                                            println!("> treeofalpha: Received tweet at {}: {:?}", current_time, tweet_message);
                                                            process_suggestions(&tweet_message.suggestions, &news_event_log, &tweet_message.body).await;
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
                                Ok(_) => println!("> treeofalpha: Ping sent successfully"),
                                Err(e) => {
                                    println!("> treeofalpha: Failed to send ping to treeofalpha: {}", e);
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



async fn calculate_averages(symbol_trade_infos: Arc<Mutex<HashMap<String, TradeInfo>>>, symbol_trade_stats: Arc<Mutex<HashMap<String, TradeStats>>>) {
    let mut interval = tokio::time::interval(Duration::from_secs(5));

    loop {
        interval.tick().await;
        let start_current_time = get_current_time();

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

        let end_current_time = get_current_time();
        // println!("*******");
        // println!("> calculate_averages: Updated averages in {}ns", end_current_time - start_current_time); // Average is 8000ns
    }
}

async fn focus_new_event_log(news_event_log: Arc<Mutex<HashMap<String, NewsEvent>>>, symbol_trade_infos: Arc<Mutex<HashMap<String, TradeInfo>>>, symbol_trade_stats: Arc<Mutex<HashMap<String, TradeStats>>>) {
    let mut interval = tokio::time::interval(Duration::from_millis(500));

    loop {
        interval.tick().await;

        let mut news_event_log_lock = news_event_log.lock().await;

        if news_event_log_lock.is_empty() {
            continue;
        }

        let start_current_time = get_current_time();

        let mut events_to_remove = Vec::new();

        // println!("*******");
        // println!("> focus_new_event_log: The length of the news event log is {}", news_event_log_lock.len());
        
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
                    
                    if current_price != 0.0{
                        if news_event.start_price == 0.0{
                            news_event.start_price = current_price.clone();
                        }
                                
                        let price_diff = ((current_price - news_event.start_price) / news_event.start_price )* 100.0;

                        if price_diff > news_event.max_price_diff_pos {
                            news_event.max_price_diff_pos = price_diff.clone();
                        }

                        if price_diff < news_event.max_price_diff_neg {
                            news_event.max_price_diff_neg = price_diff.clone();
                        }
                    }
                    let amount_of_buys_z_score = trade_stats.amount_of_buys.z_score(latest_trade_info.amount_of_buys);
                    let amount_of_sells_z_score = trade_stats.amount_of_sells.z_score(latest_trade_info.amount_of_sells);
                    let volume_sold_z_score = trade_stats.volume_sold.z_score(latest_trade_info.volume_sold);
                    let volume_bought_z_score = trade_stats.volume_bought.z_score(latest_trade_info.volume_bought);

                    let total_zscore = amount_of_buys_z_score + amount_of_sells_z_score + volume_sold_z_score + volume_bought_z_score;

                    if total_zscore > news_event.max_z_score {
                        news_event.max_z_score = total_zscore.clone();
                    }

                    if total_zscore > 10.0{
                        println!("*******");
                        println!("> focus_new_event_log: binance_symbol: {}", binance_symbol);
                        println!("> focus_new_event_log: News event title {}", news_event.news_title);    
                        println!("> focus_new_event_log: total_zscore: {}", total_zscore);
                        println!("*******");
                    }
                    
                }
            }

            // let mut trade_stats_lock = symbol_trade_stats.lock().await;

            // if let Some(trade_stats) = trade_stats_lock.get_mut(symbol) {
            //     println!("> focus_new_event_log: trade_stats.amount_of_buys Z: {}", trade_stats.amount_of_buys);
            //     println!("> focus_new_event_log: trade_stats.amount_of_sells: {}", trade_stats.amount_of_sells);
            //     println!("> focus_new_event_log: trade_stats.volume_sold: {}", trade_stats.volume_sold);
            //     println!("> focus_new_event_log: trade_stats.volume_bought: {}", trade_stats.volume_bought);
            // }

        }
        

        drop(news_event_log_lock);
        let mut news_event_log_lock = news_event_log.lock().await;

        for key in events_to_remove {
            println!("> focus_new_event_log: Removing key: {}", key);

            if let Some(news_event) = news_event_log_lock.get_mut(&key){
                println!("> focus_new_event_log: Saving news event to file");
                save_news_event_to_file(news_event).await;
            }
            news_event_log_lock.remove(&key);
        }


        let end_current_time = get_current_time();
        // println!("*******");
        // println!("> focus_new_event_log: Updated averages in {}ns", end_current_time - start_current_time);
    }
}


async fn process_suggestions(suggestions: &[Suggestion], news_event_log: &Arc<Mutex<HashMap<String, NewsEvent>>>, title: &str) {
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
                            max_z_score: 0.0,
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