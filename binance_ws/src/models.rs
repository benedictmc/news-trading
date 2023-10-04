
// Models for News Trading application
// Copyright: Benedict McGovern

use serde::Deserialize;
use std::collections::HashMap;


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
    _id: String,
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

#[derive(Debug)]
pub struct NewsEvent {
    pub binance_symbol: String,
    pub time_started: u128,
    pub news_occurance: u64,
    pub news_title: String,
    pub time_to_end: u128,
}