// Main application of the News Trading application
// Copyright: Benedict McGovern

mod models;

use models::{BinanceMessage, TradeInfo, TreeOfAlphaTweet, TreeOfAlphaNews, TradeStats, NewsEvent, Suggestion};
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
    tokio::spawn(focus_new_event_log(news_event_log.clone()));
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

    // let interval_tick = interval(Duration::from_secs(BINANCE_TICK_INTERVAL));

    loop {
        tokio::select! {
            Some(Ok(message)) = stream.next() => {

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
            }
        }
    }
}

async fn run_treeofalpha_websocket(news_event_log: Arc<Mutex<HashMap<String, NewsEvent>>>) {
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
                        match serde_json::from_str::<TreeOfAlphaNews>(&text) {
                            Ok(news_message) => {
                                let current_time = get_current_time();
                                println!("> treeofalpha: Received news at {}: {:?}", current_time, news_message);
                                process_suggestions(&news_message.suggestions, &news_event_log, &news_message.title).await;
                            },
                            Err(_) => {
                                match serde_json::from_str::<TreeOfAlphaTweet>(&text) {
                                    Ok(tweet_message) => {
                                        let current_time = get_current_time();
                                        println!("> treeofalpha: Received tweet at {}: {:?}", current_time, tweet_message);
                                        process_suggestions(&tweet_message.suggestions, &news_event_log, &tweet_message.title).await;
                                    },
                                    Err(e) => {
                                        println!("> treeofalpha: Failed to deserialize both formats: {} {}", e, text);
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



async fn calculate_averages(symbol_trade_infos: Arc<Mutex<HashMap<String, TradeInfo>>>, symbol_trade_stats: Arc<Mutex<HashMap<String, TradeStats>>>) {
    let mut interval = tokio::time::interval(Duration::from_secs(5));

    loop {
        interval.tick().await;
        // let start_current_time = get_current_time();

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

        // let end_current_time = get_current_time();
        // println!("> calculate_averages: Updated averages in {}ms", end_current_time - start_current_time);
    }
}

async fn focus_new_event_log(news_event_log: Arc<Mutex<HashMap<String, NewsEvent>>>) {
    let mut interval = tokio::time::interval(Duration::from_secs(5));

    loop {
        interval.tick().await;
        // let start_current_time = get_current_time();

        let news_event_log_lock = news_event_log.lock().await;
        println!("*******");
        println!("> focus_new_event_log: The length of the news event log is {}", news_event_log_lock.len());

        for (binance_symbol, news_event) in news_event_log_lock.iter() {
            println!("> focus_new_event_log: binance_symbol: {}", binance_symbol);
            println!("> focus_new_event_log: News event title {}", news_event.news_title);            
        }
        println!("*******");


        // let end_current_time = get_current_time();
        // println!("> calculate_averages: Updated averages in {}ms", end_current_time - start_current_time);
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
                        news_event.time_to_end = get_current_time() + 400000;
                    } else {
                        let news_event = NewsEvent {
                            binance_symbol: binance_symbol.clone(),
                            time_started: get_current_time(),
                            news_occurance: 1,
                            news_title: title.to_string(),
                            time_to_end: get_current_time() + 400000,
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