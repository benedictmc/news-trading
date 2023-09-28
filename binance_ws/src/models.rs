
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
pub struct TreeOfAlphaMessage {
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