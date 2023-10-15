
// Models for News Trading application
// Copyright: Benedict McGovern

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use phf::phf_map;
use phf::Map;

#[derive(Debug, Deserialize)]
pub struct BinanceMessage {
    pub stream: String,
    pub data: TradeData,
}

#[derive(Debug, Deserialize)]
pub struct TradeData {
    pub e: String,
    pub E: u64,
    pub s: String,
    pub a: u64,
    pub p: String,
    pub q: String,
    pub f: u64,
    pub l: u64,
    pub T: u64,
    pub m: bool,
    pub M: bool,
}

#[derive(Debug, Default)]
pub struct TradeInfo {
    pub count: usize,
    pub total_price: f64,
    pub volume_bought: f64,
    pub volume_sold: f64,
    pub amount_of_buys: u32,
    pub amount_of_sells: u32,
}

#[derive(Debug, Deserialize)]
pub struct QuotedUser {
    pub name: String,
    pub screen_name: String,
    pub icon: String,
    pub text: String,
}

#[derive(Debug, Deserialize)]
pub struct Suggestion {
    pub found: Vec<String>,
    pub coin: String,
    pub symbols: Vec<HashMap<String, String>>,
}

#[derive(Debug, Deserialize)]
pub struct TreeOfAlphaTweet {
    pub title: String,
    pub body: String,
    pub icon: String,
    pub image: String,
    pub requireInteraction: bool,
    pub r#type: String,
    pub link: String,
    pub info: HashMap<String, serde_json::Value>,
    pub suggestions: Vec<Suggestion>,
    pub time: u64,
    pub _id: String,
}

#[derive(Debug, Deserialize)]
pub struct TreeOfAlphaNews {
    actions: Vec<Action>,
    delay: u64,
    en: String,
    firstPrice: HashMap<String, f64>,
    source: String,
    pub suggestions: Vec<Suggestion>,
    symbols: Vec<String>,
    time: u64,
    pub title: String,
    url: String,
    pub _id: String,
}

#[derive(Debug, Deserialize)]
pub struct TreeOfAlphaNewsVariation {
    pub title: String,
    source: String,
    url: String,
    time: u64,
    symbols: Vec<String>,
    en: String,
    pub _id: String,
    pub suggestions: Vec<Suggestion>,
    delay: Option<u64>,
}

#[derive(Debug, Deserialize)]
struct Action {
    action: String,
    icon: Option<String>,
    title: String,
}

#[derive(Debug, Deserialize)]
struct Symbol {
    exchange: String,
    symbol: String,
}

#[derive(Debug, Deserialize)]
pub struct TradeStore {
    pub trades_buy: Vec<u32>,
    pub trades_sold: Vec<u32>,
    pub volume_buy: Vec<f64>,
    pub volume_sold: Vec<f64>,
}


pub type SymbolTradeData = HashMap<String, TradeStore>;


#[derive(Default)]
pub struct TradeTotal {
    pub total_volume_sold: f64,
    pub total_amount_of_sells: u32,
    pub total_volume_bought: f64,
    pub total_amount_of_buys: u32,
    pub times_updated: u32,
}

pub type SymbolTradeTotals = HashMap<String, TradeTotal>;

#[derive(Default)]
pub struct TradeAverage {
    pub avg_volume_sold: f64,
    pub avg_amount_of_sells: f64,
    pub avg_volume_bought: f64,
    pub avg_amount_of_buys: f64,
}

pub type SymbolTradeAverages = HashMap<String, TradeAverage>;


pub struct StatsModel {
    pub n: u32,
    pub mean: f64,
    pub m2: f64,
}

impl StatsModel {
    fn new() -> Self {
        StatsModel { n: 0, mean: 0.0, m2: 0.0 }
    }

    pub fn update<T: Into<f64>>(&mut self, x: T) {
        self.n += 1;
        let x = x.into();
        let delta = x - self.mean;
        self.mean += delta / self.n as f64;
        let delta2 = x - self.mean;
        self.m2 += delta * delta2;
    }

    pub fn variance(&self) -> f64 {
        if self.n < 2 {
            0.0
        } else {
            self.m2 / self.n as f64
        }
    }

    pub fn std_dev(&self) -> f64 {
        self.variance().sqrt()
    }

    pub fn z_score<T: Into<f64>>(&mut self, x: T) -> f64 {
        let x = x.into();
        let std_dev = self.std_dev();
        if std_dev == 0.0 {
            0.0
        } else {
            (x - self.mean) / std_dev 
        }
    }
}


pub struct TradeStats {
    pub volume_sold: StatsModel,
    pub amount_of_sells: StatsModel,
    pub volume_bought: StatsModel,
    pub amount_of_buys: StatsModel,
}

impl Default for TradeStats {
    fn default() -> Self {
        TradeStats {
            volume_sold: StatsModel::new(),
            amount_of_sells: StatsModel::new(),
            volume_bought: StatsModel::new(),
            amount_of_buys: StatsModel::new(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize)]
pub struct NewsEvent {
    pub binance_symbol: String,
    pub time_started: u128,
    pub news_occurance: u64,
    pub news_title: String,
    pub time_to_end: u128,
    pub start_price: f64,
    pub max_price_diff_neg: f64,
    pub max_price_diff_pos: f64,
    pub amount_of_buys_z_score: f64,
    pub amount_of_sells_z_score: f64,
    pub volume_sold_z_score: f64,
    pub volume_bought_z_score: f64,
    pub total_z_score: f64,
    pub news_id: String,
}

#[derive(Deserialize)]
struct Config {
    api_key: String,
    api_secret: String,
}

#[derive(Debug, Deserialize)]
pub struct BinanceError {
    pub code: i64,
    pub msg: String,
}

#[derive(Debug, Deserialize)]
pub struct BinanceTradeInfo {
    pub news_id: String,
    pub z_score: f64,
    pub symbol: String,
    pub price: f64,
    pub side: String,
    pub quantity: f64,
    pub leverage: i32,
    pub stop_loss_price: f64,
    pub take_profit_price: f64,
}


#[derive(Debug, Deserialize)]
pub struct SymbolInfo {
    pub quantity_precision: u8,
    pub price_precision: u8,
}

pub static SYMBOLS_INFO: Map<&'static str, SymbolInfo> = phf_map! {
    "BTCUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 1 },
    "ETHUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 2 },
    "BCHUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 2 },
    "XRPUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "EOSUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "LTCUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 2 },
    "TRXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "ETCUSDT" =>  SymbolInfo { quantity_precision: 2, price_precision: 3 },
    "LINKUSDT" =>  SymbolInfo { quantity_precision: 2, price_precision: 3 },
    "XLMUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "ADAUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "XMRUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 2 },
    "DASHUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 2 },
    "ZECUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 2 },
    "XTZUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "BNBUSDT" =>  SymbolInfo { quantity_precision: 2, price_precision: 2 },
    "ATOMUSDT" =>  SymbolInfo { quantity_precision: 2, price_precision: 3 },
    "ONTUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "IOTAUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "BATUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "VETUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "NEOUSDT" =>  SymbolInfo { quantity_precision: 2, price_precision: 3 },
    "QTUMUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "IOSTUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "THETAUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "ALGOUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "ZILUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "KNCUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "ZRXUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "COMPUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 2 },
    "OMGUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "DOGEUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "SXPUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "KAVAUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "BANDUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "RLCUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "WAVESUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "MKRUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 1 },
    "SNXUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "DOTUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "DEFIUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 1 },
    "YFIUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 0 },
    "BALUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "CRVUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "TRBUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "RUNEUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "SUSHIUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "SRMUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "EGLDUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 2 },
    "SOLUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "ICXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "STORJUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "BLZUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "UNIUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "AVAXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "FTMUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "HNTUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "ENJUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "FLMUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "TOMOUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "RENUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "KSMUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 2 },
    "NEARUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "AAVEUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 2 },
    "FILUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "RSRUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "LRCUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "MATICUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "OCEANUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "CVCUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "BELUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "CTKUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "AXSUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "ALPHAUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "ZENUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "SKLUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "GRTUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "1INCHUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "CHZUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "SANDUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "ANKRUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "BTSUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "LITUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "UNFIUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "REEFUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "RVNUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "SFPUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "XEMUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "BTCSTUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "COTIUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "CHRUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "MANAUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "ALICEUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "HBARUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "ONEUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "LINAUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "STMXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "DENTUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "CELRUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "HOTUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "MTLUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "OGNUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "NKNUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "SCUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "DGBUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "1000SHIBUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "BAKEUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "GTCUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "BTCDOMUSDT" =>  SymbolInfo { quantity_precision: 3, price_precision: 1 },
    "IOTXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "AUDIOUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "RAYUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "C98USDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "MASKUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "ATAUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "DYDXUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "1000XECUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "GALAUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "CELOUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "ARUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "KLAYUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "ARPAUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "CTSIUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "LPTUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "ENSUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "PEOPLEUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "ANTUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "ROSEUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "DUSKUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "FLOWUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "IMXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "API3USDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "GMTUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "APEUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "WOOUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "FTTUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "JASMYUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "DARUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "GALUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "OPUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "INJUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "STGUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "SPELLUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 7 },
    "1000LUNCUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "LUNA2USDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "LDOUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "CVXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "ICPUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "APTUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "QNTUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 2 },
    "BLUEBIRDUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "FETUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "FXSUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "HOOKUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "MAGICUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "TUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "RNDRUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "HIGHUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "MINAUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "ASTRUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "AGIXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "PHBUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "GMXUSDT" =>  SymbolInfo { quantity_precision: 2, price_precision: 2 },
    "CFXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "STXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "COCOSUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "BNXUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "ACHUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "SSVUSDT" =>  SymbolInfo { quantity_precision: 2, price_precision: 2 },
    "CKBUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "PERPUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "TRUUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "LQTYUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "USDCUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "IDUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "ARBUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "JOEUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "TLMUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "AMBUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "LEVERUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "RDNTUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "HFTUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "XVSUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 3 },
    "BLURUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "EDUUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "IDEXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "SUIUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "1000PEPEUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 7 },
    "1000FLOKIUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "UMAUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "RADUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 3 },
    "KEYUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "COMBOUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 4 },
    "NMRUSDT" =>  SymbolInfo { quantity_precision: 1, price_precision: 2 },
    "MDTUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
    "XVGUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 6 },
    "WLDUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "PENDLEUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "ARKMUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "AGLDUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "YGGUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 4 },
    "DODOXUSDT" =>  SymbolInfo { quantity_precision: 0, price_precision: 5 },
};